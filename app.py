import os
import json
import time
import math
from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)
DATA_DIR = os.path.expanduser("~/.local/share/opencode/storage/message")

def get_session_stats(session_path):
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
    
    valid_token_messages = 0
    has_cost_data = False
    
    # Finish reason (from last assistant message)
    finish_reason = None

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
             
        # Track model usage
        if model != "Unknown":
            if model not in models_used:
                models_used[model] = {'tokens': 0, 'cost': 0.0}
        
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
        
        if model != "Unknown":
            models_used[model]['tokens'] += (msg_input + msg_output)
            models_used[model]['cost'] += msg_cost
            
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
        "finish_reason": finish_reason
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sessions')
def sessions():
    sessions_data = []
    
    # Daily aggregation
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_ts = int(today_start.timestamp() * 1000)
    
    today_cost = 0.0
    today_tokens = 0
    active_count = 0
    
    if os.path.exists(DATA_DIR):
        try:
             session_dirs = [d for d in os.listdir(DATA_DIR) if d.startswith('ses_')]
             
             for d in session_dirs:
                 path = os.path.join(DATA_DIR, d)
                 if os.path.isdir(path):
                     stats = get_session_stats(path)
                     if stats:
                         sessions_data.append(stats)
                         
                         if stats['status'] == 'Active':
                             active_count += 1
                         
                         if stats['timestamp'] > today_start_ts:
                             today_cost += stats['cost_val']
                             today_tokens += stats['total_tokens']

        except Exception as e:
            return jsonify({"error": str(e)})

    # Sort by timestamp descending (newest first)
    sessions_data.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({
        "sessions": sessions_data,
        "metrics": {
            "today_cost": f"${today_cost:.2f}",
            "today_tokens": today_tokens,
            "active_count": active_count
        }
    })

if __name__ == '__main__':
    # Run on 0.0.0.0:38002
    app.run(host='0.0.0.0', port=38002, debug=True)
