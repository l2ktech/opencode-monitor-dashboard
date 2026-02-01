# pyright: reportOperatorIssue=false
import os
import json
import time
import math
import requests
from typing import Optional, Dict, Any, cast, List
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta

app = Flask(__name__)
DATA_DIR = os.path.expanduser("~/.local/share/opencode/storage/message")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard-config.json')

def get_session_stats(session_path: str) -> Optional[Dict[str, Any]]:
    session_id = os.path.basename(session_path)
    messages = []
    try:
        # Read all json files in the session directory
        files = [f for f in os.listdir(session_path) if f.endswith(".json")]
        if not files:
            return None
            
        for f in files:
            try:
                with open(os.path.join(session_path, f), 'r') as file:
                    messages.append(json.load(file))
            except Exception:
                continue # Skip malformed files
    except FileNotFoundError:
        return None

    if not messages:
        return None

    # Sort by time.created
    messages.sort(key=lambda x: x.get('time', {}).get('created', 0))

    first_msg = messages[0]
    last_msg = messages[-1]

    start_time_ms = first_msg.get('time', {}).get('created', 0)
    
    # Try to find completion time of the last message, or use its creation time
    end_time_ms = last_msg.get('time', {}).get('completed', last_msg.get('time', {}).get('created', start_time_ms))
    
    # Calculate duration
    duration_ms = end_time_ms - start_time_ms
    # Format duration nicely
    seconds_total = int(duration_ms / 1000)
    m, s = divmod(seconds_total, 60)
    h, m = divmod(m, 60)
    duration_str = "{:02d}:{:02d}:{:02d}".format(h, m, s)
    duration_formatted = f"{h}h {m}m" if h > 0 else f"{m}m {s}s"
    if h == 0 and m == 0:
        duration_formatted = f"{s}s"

    # Get Name/Title
    session_name = session_id # Default
    if first_msg.get('summary') and first_msg['summary'].get('title'):
         session_name = first_msg['summary']['title']
    
    # Get Model, Provider, Agent
    model = "Unknown"
    provider = "Unknown"
    agent = "Unknown"
    
    interactions = 0
    message_count = len(messages)
    
    # Project path
    project_path = "Unknown"
    
    input_tokens = 0
    output_tokens = 0
    cache_write_tokens = 0
    cache_read_tokens = 0
    total_cost = 0.0
    
    # New metrics
    reasoning_tokens = 0
    files_changed = 0
    lines_added = 0
    lines_deleted = 0
    
    # Latency calculation
    total_latency = 0
    latency_count = 0
    
    models_used = {} # {model_name: {'tokens': 0, 'cost': 0}}
    agent_stats = {}
    model_stats = {}
    
    valid_token_messages = 0
    has_cost_data = False
    
    # Finish reason (from last assistant message)
    finish_reason = None

    def ensure_stats(container, key):
        if key not in container:
            container[key] = {
                'calls': 0,
                'success': 0,
                'failed': 0,
                'tool_calls': 0,
                'length': 0,
                'other': 0,
                'tokens': 0,
                'cost': 0.0
            }
        return container[key]

    for m in messages:
        # Basic stats
        if m.get('role') == 'user':
            interactions += 1
        elif m.get('role') == 'assistant':
            # Check for finish reason in assistant messages
            if 'finish' in m:
                finish_reason = m['finish']
            
            # Latency
            if m.get('time', {}).get('completed') and m.get('time', {}).get('created'):
                latency = m['time']['completed'] - m['time']['created']
                if latency > 0:
                    total_latency += latency
                    latency_count += 1
            
        if 'path' in m and 'cwd' in m['path']:
            project_path = m['path']['cwd']
            
        if 'agent' in m:
             agent = m['agent']
         
        if 'modelID' in m:
             model = m['modelID']
        if 'providerID' in m:
             provider = m['providerID']
             
        if 'model' in m and isinstance(m['model'], dict):
             model = m['model'].get('modelID', model)
             provider = m['model'].get('providerID', provider)

        msg_model = "Unknown"
        if 'modelID' in m:
             msg_model = m['modelID']
        if 'model' in m and isinstance(m['model'], dict):
             msg_model = m['model'].get('modelID', msg_model)
             
        # Track model usage
        if msg_model != "Unknown":
            if msg_model not in models_used:
                models_used[msg_model] = {'tokens': 0, 'cost': 0.0}
        
        msg_input = 0
        msg_output = 0
        msg_cost = 0.0
        
        # Tokens
        if m.get('tokens') is not None and isinstance(m['tokens'], dict):
            valid_token_messages += 1
            msg_input = m['tokens'].get('input', 0) or 0
            msg_output = m['tokens'].get('output', 0) or 0
            cache_write_tokens += m['tokens'].get('cache', {}).get('write', 0) or 0
            cache_read_tokens += m['tokens'].get('cache', {}).get('read', 0) or 0
            
            # Reasoning
            if m['tokens'].get('reasoning'):
                reasoning_tokens += m['tokens']['reasoning']
            
            input_tokens += msg_input
            output_tokens += msg_output
        
        if m.get('cost') is not None:
            has_cost_data = True
            msg_cost = m.get('cost', 0)
        
        total_cost += msg_cost
        
        if msg_model != "Unknown":
            models_used[msg_model]['tokens'] += (msg_input + msg_output)
            models_used[msg_model]['cost'] += msg_cost

        if m.get('role') == 'assistant':
            msg_agent = m.get('agent', 'Unknown')
            finish = m.get('finish')
            has_msg_error = bool(m.get('error'))

            agent_entry = ensure_stats(agent_stats, msg_agent)
            agent_entry['calls'] += 1
            if has_msg_error:
                agent_entry['failed'] += 1
            elif finish == 'stop':
                agent_entry['success'] += 1
            elif finish == 'tool-calls':
                agent_entry['tool_calls'] += 1
            elif finish == 'length':
                agent_entry['length'] += 1
            else:
                agent_entry['other'] += 1
            agent_entry['tokens'] += (msg_input + msg_output)
            agent_entry['cost'] += msg_cost

            model_entry = ensure_stats(model_stats, msg_model)
            model_entry['calls'] += 1
            if has_msg_error:
                model_entry['failed'] += 1
            elif finish == 'stop':
                model_entry['success'] += 1
            elif finish == 'tool-calls':
                model_entry['tool_calls'] += 1
            elif finish == 'length':
                model_entry['length'] += 1
            else:
                model_entry['other'] += 1
            model_entry['tokens'] += (msg_input + msg_output)
            model_entry['cost'] += msg_cost
            
        # File changes (check latest summary)
        if 'summary' in m and isinstance(m['summary'], dict):
            # We take the latest summary values found? 
            # Usually summary is cumulative or per-turn diffs?
            # Assuming 'diffs' logic in prompt: "files_changed += msg['summary'].get('files', 0)" implies cumulative scan
            # But normally summary is per message.
            # Let's accumulate if it looks like a diff report
            s = m['summary']
            files_changed += s.get('files', 0)
            lines_added += s.get('additions', 0)
            lines_deleted += s.get('deletions', 0)

    has_token_data = valid_token_messages > 0

    # Format models_used for frontend
    models_list = []
    for m_name, data in models_used.items():
        models_list.append({
            'name': m_name,
            'tokens': data['tokens'],
            'cost': f"${data['cost']:.2f}"
        })

    # Recent tokens
    recent_tokens = {
        'input': 0,
        'output': 0,
        'cache_write': 0,
        'cache_read': 0
    }
    
    # Find last message with valid tokens
    for m in reversed(messages):
        if m.get('tokens') is not None and isinstance(m['tokens'], dict):
            recent_tokens['input'] = m['tokens'].get('input', 0) or 0
            recent_tokens['output'] = m['tokens'].get('output', 0) or 0
            recent_tokens['cache_write'] = m['tokens'].get('cache', {}).get('write', 0) or 0
            recent_tokens['cache_read'] = m['tokens'].get('cache', {}).get('read', 0) or 0
            break

    # Calculate tokens per minute
    minutes = duration_ms / 1000 / 60
    tokens_per_minute = 0
    if minutes > 0:
        tokens_per_minute = int((input_tokens + output_tokens) / minutes)
        
    rate_level = "LOW"
    if tokens_per_minute > 50000:
        rate_level = "HIGH"
    elif tokens_per_minute > 10000:
        rate_level = "MEDIUM"

    # Context window logic
    # 1. Current Turn Context (What actually hits the window limit)
    # The context sent to model in the latest interaction
    current_turn_context = recent_tokens['input'] + recent_tokens['cache_read']
    
    # 2. Total Accumulated Context (Historical usage sum)
    total_accumulated_context = input_tokens + cache_read_tokens
    
    context_window = 200000 # Default
    if 'gemini' in model.lower() and 'pro' in model.lower():
         context_window = 2000000
    elif 'claude' in model.lower():
         context_window = 200000
    
    context_percentage = 0
    if context_window > 0:
        # Progress bar based on CURRENT turn usage vs Limit
        context_percentage = min(100, int((current_turn_context / context_window) * 100))

    context_remaining = max(0, context_window - current_turn_context)
    context_overage = max(0, current_turn_context - context_window)
    context_compact_needed = context_overage if context_overage > 0 else 0

    # Time percentage
    max_duration_seconds = 5 * 3600
    time_percentage = min(100, int((seconds_total / max_duration_seconds) * 100))

    # Extract latest message text/summary
    latest_message_preview = "No content"
    if 'text' in last_msg:
         latest_message_preview = last_msg['text']
    elif 'content' in last_msg:
         latest_message_preview = last_msg['content']
    
    if isinstance(latest_message_preview, str):
        latest_message_preview = latest_message_preview[:200]
    else:
        latest_message_preview = str(latest_message_preview)[:200]

    # Check for errors
    has_error = False
    if last_msg.get('error'):
        has_error = True

    # Determine status
    last_activity_ms = end_time_ms
    last_activity_dt = datetime.fromtimestamp(last_activity_ms / 1000)
    now = datetime.now()
    is_recent = (now - last_activity_dt) < timedelta(minutes=15)
    
    status = "Completed"
    last_role = last_msg.get('role', '')
    last_completed = last_msg.get('time', {}).get('completed')
    
    if is_recent:
        if last_role == 'user':
            status = "Active"
        elif last_role == 'assistant' and not last_completed:
            status = "Active"
    
    # Time since last activity friendly string
    delta = now - last_activity_dt
    seconds_since_activity = int(delta.total_seconds())
    if delta.days > 0:
        time_since = f"{delta.days}天前"
    elif delta.seconds > 3600:
        time_since = f"{delta.seconds // 3600}小时前"
    elif delta.seconds > 60:
        time_since = f"{delta.seconds // 60}分钟前"
    else:
        time_since = f"{delta.seconds}秒前"

    # Last message duration
    last_msg_duration_ms = 0
    if last_msg.get('time', {}).get('completed') and last_msg.get('time', {}).get('created'):
         last_msg_duration_ms = last_msg['time']['completed'] - last_msg['time']['created']
    last_msg_duration_s = int(last_msg_duration_ms / 1000)

    # Derived Metrics
    avg_latency = (total_latency / latency_count / 1000) if latency_count > 0 else 0
    
    cache_hit_rate = 0
    if (input_tokens + cache_read_tokens) > 0:
        cache_hit_rate = int((cache_read_tokens / (input_tokens + cache_read_tokens)) * 100)
    
    # Savings: Assuming generic ~$3/M input vs $0.3/M cache -> saving $2.7 per M
    # This is a rough estimation for visualization
    cache_savings = (cache_read_tokens / 1000000) * 2.7

    return {
        "id": session_id,
        "started": datetime.fromtimestamp(start_time_ms / 1000).strftime('%Y-%m-%d %H:%M:%S'),
        "timestamp": start_time_ms,
        "duration": duration_str,
        "duration_formatted": duration_formatted,
        "name": session_name,
        "model": model,
        "provider": provider,
        "agent": agent,
        "status": status,
        "message_count": message_count,
        "project_path": project_path,
        "last_activity": datetime.fromtimestamp(last_activity_ms / 1000).strftime('%Y-%m-%d %H:%M:%S'),
        "time_since_activity": time_since,
        "seconds_since_activity": seconds_since_activity,
        "interactions": interactions,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_write_tokens": cache_write_tokens,
        "cache_read_tokens": cache_read_tokens,
        "total_tokens": input_tokens + output_tokens,
        "recent_tokens": recent_tokens,
        "tokens_per_minute": tokens_per_minute,
        "rate_level": rate_level,
        "context_size": current_turn_context,  # Legacy support if needed, but updated to current turn
        "current_turn_context": current_turn_context,
        "total_accumulated_context": total_accumulated_context,
        "context_window": context_window,
        "context_percentage": context_percentage,
        "context_remaining": context_remaining,
        "context_overage": context_overage,
        "context_compact_needed": context_compact_needed,
        "time_percentage": time_percentage,
        "cost": f"${total_cost:.4f}",
        "cost_val": total_cost,
        "latest_preview": latest_message_preview,
        "has_error": has_error,
        "latest_duration": f"{last_msg_duration_s}s",
        "models_used": models_list,
        "has_token_data": has_token_data,
        "has_cost_data": has_cost_data,
        
        # New Metrics
        "avg_latency": f"{avg_latency:.1f}",
        "has_latency": avg_latency > 0,
        "cache_hit_rate": cache_hit_rate,
        "cache_savings": f"{cache_savings:.2f}",
        "has_cache_data": cache_read_tokens > 0,
        "reasoning_tokens": reasoning_tokens,
        "has_reasoning": reasoning_tokens > 0,
        "files_changed": files_changed,
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
        "has_file_changes": files_changed > 0,
        "finish_reason": finish_reason,
        "agent_stats": agent_stats,
        "model_stats": model_stats
    }

def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_FILE):
        return {"devices": []}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"devices": []}

def fetch_remote_sessions(device_url: str) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(f"{device_url}/api/sessions", timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/devices')
def get_devices():
    config = load_config()
    return jsonify({"devices": config.get("devices", [])})

@app.route('/api/sessions')
def sessions():
    sessions_data = []
    overall_agent_stats = {}
    overall_model_stats = {}

    def to_int(value: object) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            try:
                return int(float(value))
            except ValueError:
                return 0
        return 0

    def to_float(value: object) -> float:
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0

    def is_recent(timestamp_val: object, today_start_ts_val: int) -> bool:
        if isinstance(timestamp_val, bool):
            return int(timestamp_val) > today_start_ts_val
        if isinstance(timestamp_val, (int, float)):
            return int(timestamp_val) > today_start_ts_val
        if isinstance(timestamp_val, str):
            try:
                return int(float(timestamp_val)) > today_start_ts_val
            except ValueError:
                return False
        return False

    def merge_stats(target, source):
        for key, stats in source.items():
            if key not in target:
                target[key] = {
                    'calls': 0,
                    'success': 0,
                    'failed': 0,
                    'tool_calls': 0,
                    'length': 0,
                    'other': 0,
                    'tokens': 0,
                    'cost': 0.0
                }
            calls = to_int(stats.get('calls'))
            success = to_int(stats.get('success'))
            failed = to_int(stats.get('failed'))
            tool_calls = to_int(stats.get('tool_calls'))
            length = to_int(stats.get('length'))
            other = to_int(stats.get('other'))
            tokens = to_int(stats.get('tokens'))
            cost = to_float(stats.get('cost'))

            target_entry = target[key]
            if not isinstance(target_entry, dict):
                continue

            entry_calls = to_int(target_entry.get('calls')) or 0
            entry_success = to_int(target_entry.get('success')) or 0
            entry_failed = to_int(target_entry.get('failed')) or 0
            entry_tool_calls = to_int(target_entry.get('tool_calls')) or 0
            entry_length = to_int(target_entry.get('length')) or 0
            entry_other = to_int(target_entry.get('other')) or 0
            entry_tokens = to_int(target_entry.get('tokens')) or 0
            entry_cost = to_float(target_entry.get('cost')) or 0.0

            if isinstance(calls, int):
                target_entry['calls'] = entry_calls + calls
            if isinstance(success, int):
                target_entry['success'] = entry_success + success
            if isinstance(failed, int):
                target_entry['failed'] = entry_failed + failed
            if isinstance(tool_calls, int):
                target_entry['tool_calls'] = entry_tool_calls + tool_calls
            if isinstance(length, int):
                target_entry['length'] = entry_length + length
            if isinstance(other, int):
                target_entry['other'] = entry_other + other
            if isinstance(tokens, int):
                target_entry['tokens'] = entry_tokens + tokens
            if isinstance(cost, (int, float)):
                target_entry['cost'] = float(entry_cost) + float(cost)
    
    # Daily aggregation
    today_start: datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_ts: int = int(today_start.timestamp() * 1000)
    
    today_cost: float = 0.0
    today_tokens: int = 0
    active_count: int = 0
    by_device_stats = {}
    
    config = load_config()
    devices = config.get('devices', [])
    
    for device in devices:
        if not device.get('enabled', True):
            continue
            
        device_id = device.get('id', 'unknown')
        device_name = device.get('name', device_id)
        device_url = device.get('url', '')
        
        if device_url == 'local':
            by_device_stats[device_id] = {'name': device_name, 'sessions': 0, 'cost': 0.0, 'tokens': 0, 'active': 0}
        else:
            remote_data = fetch_remote_sessions(device_url)
            if remote_data:
                remote_sessions = remote_data.get('sessions', [])
                for session in remote_sessions:
                    session['device_id'] = device_id
                    session['device_name'] = device_name
                    sessions_data.append(session)
                    
                    merge_stats(overall_agent_stats, session.get('agent_stats', {}))
                    merge_stats(overall_model_stats, session.get('model_stats', {}))
                    
                    if session.get('status') == 'Active':
                        active_count += 1
                    
                    if is_recent(session.get('timestamp'), today_start_ts):
                        today_cost += to_float(session.get('cost_val'))
                        today_tokens += to_int(session.get('total_tokens'))
    
    if os.path.exists(DATA_DIR):
        try:
            session_dirs = [d for d in os.listdir(DATA_DIR) if d.startswith('ses_')]
            
            for d in session_dirs:
                path = os.path.join(DATA_DIR, d)
                if os.path.isdir(path):
                    stats = get_session_stats(path)
                    if isinstance(stats, dict):
                        stats_dict: Dict[str, Any] = stats
                        stats_dict['device_id'] = 'local'
                        stats_dict['device_name'] = '本地设备'
                        sessions_data.append(stats_dict)

                        merge_stats(overall_agent_stats, stats_dict.get('agent_stats', {}))
                        merge_stats(overall_model_stats, stats_dict.get('model_stats', {}))
                        
                        stats_status = stats_dict.get('status')
                        if stats_status == 'Active':
                            active_count += 1
                        
                        if is_recent(stats_dict.get('timestamp'), today_start_ts):
                            stats_cost_val: float = to_float(stats_dict.get('cost_val'))
                            today_cost = float(today_cost) + stats_cost_val

                            stats_tokens_val: int = to_int(stats_dict.get('total_tokens'))
                            today_tokens = int(today_tokens) + stats_tokens_val

        except Exception as e:
            return jsonify({"error": str(e)})

    # Sort by timestamp descending (newest first)
    sessions_data.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({
        "sessions": sessions_data,
        "metrics": {
            "today_cost": f"${today_cost:.2f}",
            "today_tokens": today_tokens,
            "active_count": active_count,
            "agent_stats": overall_agent_stats,
            "model_stats": overall_model_stats
        }
    })

if __name__ == '__main__':
    # Run on 0.0.0.0:38002
    app.run(host='0.0.0.0', port=38002, debug=True)
