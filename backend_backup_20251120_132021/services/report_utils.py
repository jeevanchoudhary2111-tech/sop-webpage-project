# backend/services/report_utils.py

from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def generate_sop_backup_html_report(activities, sop_type, admin_username):
    """Generate comprehensive HTML backup report for SOP reset"""

    # Group activities by date and user
    grouped_data = {}
    for activity in activities:
        date_key = activity["completed_at"].strftime("%Y-%m-%d")
        if date_key not in grouped_data:
            grouped_data[date_key] = {}
        
        username = activity["username"]
        if username not in grouped_data[date_key]:
            grouped_data[date_key][username] = []
        
        grouped_data[date_key][username].append(activity)
    
    # --- ADDED LOGGING ---
    logger.info(f"Grouped data for SOP backup report: {grouped_data}")
    # --- END ADDED LOGGING ---

    # Calculate statistics
    total_activities = len(activities)
    unique_users = len(set(a["username"] for a in activities))
    unique_tasks = len(set(a["task_id"] for a in activities))
    date_range = f"{min(a['completed_at'] for a in activities).strftime('%Y-%m-%d')} to {max(a['completed_at'] for a in activities).strftime('%Y-%m-%d')}" if activities else "No activities"
    
    # Generate HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SOP Backup Report - {sop_type.upper()}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @media print {{
                .no-print {{ display: none; }}
                body {{ margin: 0; padding: 20px; }}
            }}
            .page-break {{ page-break-before: always; }}
        </style>
    </head>
    <body class="bg-gray-50 text-gray-800">
        <div class="max-w-6xl mx-auto bg-white shadow-lg rounded-lg overflow-hidden">
            <!-- Header -->
            <div class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-8">
                <div class="flex justify-between items-start">
                    <div>
                        <h1 class="text-3xl font-bold mb-2">📋 SOP Backup Report</h1>
                        <p class="text-blue-100 text-lg">{sop_type.replace('_', ' ').title()}</p>
                    </div>
                    <div class="text-right text-blue-100">
                        <p class="text-sm">Generated on</p>
                        <p class="text-lg font-semibold">{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                        <p class="text-sm mt-2">Reset by: <span class="font-semibold">{admin_username}</span></p>
                    </div>
                </div>
            </div>
            
            <!-- Summary Statistics -->
            <div class="p-8 border-b border-gray-200">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">📊 Summary Statistics</h2>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
                    <div class="bg-blue-50 rounded-lg p-4 text-center">
                        <div class="text-3xl font-bold text-blue-600">{total_activities}</div>
                        <div class="text-sm text-gray-600 mt-1">Total Activities</div>
                    </div>
                    <div class="bg-green-50 rounded-lg p-4 text-center">
                        <div class="text-3xl font-bold text-green-600">{unique_users}</div>
                        <div class="text-sm text-gray-600 mt-1">Active Users</div>
                    </div>
                    <div class="bg-purple-50 rounded-lg p-4 text-center">
                        <div class="text-3xl font-bold text-purple-600">{unique_tasks}</div>
                        <div class="text-sm text-gray-600 mt-1">Unique Tasks</div>
                    </div>
                    <div class="bg-yellow-50 rounded-lg p-4 text-center">
                        <div class="text-3xl font-bold text-yellow-600">{len(grouped_data)}</div>
                        <div class="text-sm text-gray-600 mt-1">Active Days</div>
                    </div>
                </div>
                <div class="mt-4 text-center text-gray-600">
                    <p><strong>Date Range:</strong> {date_range}</p>
                </div>
            </div>
            
            <!-- Detailed Activities -->
            <div class="p-8">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">📅 Detailed Activities</h2>
    """
    
    # Add activities grouped by date
    for date_key in sorted(grouped_data.keys(), reverse=True):
        date_obj = datetime.strptime(date_key, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%A, %B %d, %Y")
        
        html_content += f"""
                <div class="mb-8 border border-gray-200 rounded-lg overflow-hidden">
                    <div class="bg-gray-100 px-6 py-4 border-b border-gray-200">
                        <h3 class="text-lg font-semibold text-gray-900">📅 {formatted_date}</h3>
                        <p class="text-sm text-gray-600">{sum(len(tasks) for tasks in grouped_data[date_key].values())} activities</p>
                    </div>
                    <div class="p-6">
        """
        
        for username in sorted(grouped_data[date_key].keys()):
            user_activities = grouped_data[date_key][username]
            html_content += f"""
                        <div class="mb-6 last:mb-0">
                            <div class="flex items-center mb-3">
                                <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-semibold mr-3">
                                    {username[0].upper()}
                                </div>
                                <h4 class="text-lg font-semibold text-gray-900">{username}</h4>
                                <span class="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full">
                                    {len(user_activities)} tasks
                                </span>
                            </div>
                            <div class="ml-11 space-y-2">
            """
            
            for activity in sorted(user_activities, key=lambda x: x["completed_at"]):
                time_str = activity["completed_at"].strftime("%I:%M %p")
                html_content += f"""
                                <div class="flex items-start py-2 border-l-2 border-green-400 pl-4 bg-green-50 rounded-r">
                                    <div class="flex-shrink-0 w-2 h-2 bg-green-400 rounded-full mt-2 mr-3"></div>
                                    <div class="flex-grow">
                                        <p class="text-sm font-medium text-gray-900">{activity["task_description"]}</p>
                                        <p class="text-xs text-gray-500 mt-1">
                                            <span class="font-mono bg-gray-100 px-2 py-1 rounded">{activity["task_id"]}</span>
                                            <span class="ml-2">⏰ {time_str}</span>
                                        </p>
                                    </div>
                                </div>
                """
            
            html_content += """
                            </div>
                        </div>
            """
        
        html_content += """
                    </div>
                </div>
        """
    
    # Add task summary
    task_summary = {}
    for activity in activities:
        task_id = activity["task_id"]
        if task_id not in task_summary:
            task_summary[task_id] = {
                "description": activity["task_description"],
                "count": 0,
                "users": set()
            }
        task_summary[task_id]["count"] += 1
        task_summary[task_id]["users"].add(activity["username"])
    
    # --- ADDED LOGGING ---
    logger.info(f"Task summary for SOP backup report: {task_summary}")
    # --- END ADDED LOGGING ---

    html_content += f"""
            </div>
            
            <!-- Task Summary -->
            <div class="p-8 bg-gray-50 border-t border-gray-200">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">📋 Task Summary</h2>
                <div class="grid gap-4">
    """
    
    for task_id, info in sorted(task_summary.items()):
        html_content += f"""
                    <div class="bg-white rounded-lg p-4 border border-gray-200">
                        <div class="flex justify-between items-start">
                            <div class="flex-grow">
                                <h4 class="font-semibold text-gray-900">{info["description"]}</h4>
                                <p class="text-sm text-gray-600 font-mono mt-1">{task_id}</p>
                            </div>
                            <div class="text-right ml-4">
                                <div class="text-lg font-bold text-blue-600">{info["count"]}</div>
                                <div class="text-xs text-gray-500">completions</div>
                                <div class="text-xs text-gray-500 mt-1">{len(info["users"])} users</div>
                            </div>
                        </div>
                    </div>
        """
    
    html_content += """
                </div>
            </div>
            
            <!-- Footer -->
            <div class="p-6 bg-gray-800 text-white text-center">
                <p class="text-sm">
                    🔒 This backup was automatically generated before SOP reset
                </p>
                <p class="text-xs text-gray-400 mt-2">
                    SOP Tracking System - Confidential Data
                </p>
            </div>
        </div>
        
        <!-- Print Button -->
        <div class="no-print text-center mt-8 mb-4">
            <button onclick="window.print()" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold shadow-lg transition duration-200">
                🖨️ Print This Report
            </button>
        </div>
    </body>
    </html>
    """
    return html_content

def generate_us_position_html_report(us_data, admin_username):
    """Generate HTML report for US Position data"""

    report_date = us_data.get("date", "N/A")
    last_updated_by = us_data.get("last_updated_by", "N/A")
    last_updated_at = us_data.get("last_updated_at", datetime.now()).strftime('%B %d, %Y at %I:%M %p')
    form_data = us_data.get("form_data", {})

    # Group data by time slot for table display
    grouped_by_time = {}
    notes = ""

    for key, item in form_data.items():
        if item.get("field_type") == "notes":
            notes = item.get("value", "")
            continue

        time_slot = item.get("time_slot", "Unknown Time")
        section_type = item.get("section_type", "Unknown Section")
        field_type = item.get("field_type", "Unknown Field")
        value = item.get("value", "")
        username = item.get("username", "N/A")
        # Ensure filled_at is a datetime object before formatting
        filled_at_raw = item.get("filled_at")
        filled_at = datetime.fromisoformat(filled_at_raw).strftime('%I:%M %p') if filled_at_raw else "N/A"

        if time_slot not in grouped_by_time:
            grouped_by_time[time_slot] = {
                "OMS": {},
                "Live Sheet": {},
                "IB": {},
                "Margin": {"value": "", "username": "N/A", "filled_at": "N/A"}
            }

        if section_type == "Margin":
            grouped_by_time[time_slot]["Margin"] = {
                "value": value,
                "username": username,
                "filled_at": filled_at
            }
        else:
            if field_type not in grouped_by_time[time_slot][section_type]:
                grouped_by_time[time_slot][section_type][field_type] = {
                    "value": value,
                    "username": username,
                    "filled_at": filled_at
                }

    # Sort time slots for consistent display
    # This sorting logic assumes times are in 12-hour format with AM/PM or can be directly compared.
    # For more robust sorting, consider converting to 24-hour format or datetime objects.
    # Using a custom sort key for robustness with AM/PM
    def time_sort_key(time_str):
        try:
            return datetime.strptime(time_str, '%I:%M %p')
        except ValueError:
            return time_str # Fallback for non-standard times

    sorted_times = sorted(grouped_by_time.keys(), key=time_sort_key)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>US Position Report - {report_date}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @media print {{
                .no-print {{ display: none; }}
                body {{ margin: 0; padding: 20px; }}
            }}
            .page-break {{ page-break-before: always; }}
            .tooltip {{
                position: relative;
                display: inline-block;
            }}
            .tooltip .tooltiptext {{
                visibility: hidden;
                width: 120px;
                background-color: #333;
                color: #fff;
                text-align: center;
                border-radius: 6px;
                padding: 5px 0;
                position: absolute;
                z-index: 1;
                bottom: 125%; /* Top */
                left: 50%;
                margin-left: -60px;
                opacity: 0;
                transition: opacity 0.3s;
            }}
            .tooltip .tooltiptext::after {{
                content: " ";
                position: absolute;
                top: 100%; /* At the bottom of the tooltip */
                left: 50%;
                margin-left: -5px;
                border-width: 5px;
                border-style: solid;
                border-color: #333 transparent transparent transparent;
            }}
            .tooltip:hover .tooltiptext {{
                visibility: visible;
                opacity: 1;
            }}
        </style>
    </head>
    <body class="bg-gray-50 text-gray-800">
        <div class="max-w-6xl mx-auto bg-white shadow-lg rounded-lg overflow-hidden">
            <!-- Header -->
            <div class="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-8">
                <div class="flex justify-between items-start">
                    <div>
                        <h1 class="text-3xl font-bold mb-2">🇺🇸 US Position Report</h1>
                        <p class="text-purple-100 text-lg">Data for {report_date}</p>
                    </div>
                    <div class="text-right text-purple-100">
                        <p class="text-sm">Generated on</p>
                        <p class="text-lg font-semibold">{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                        <p class="text-sm mt-2">Report requested by: <span class="font-semibold">{admin_username}</span></p>
                    </div>
                </div>
            </div>
            
            <!-- Summary -->
            <div class="p-8 border-b border-gray-200">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">📊 Summary</h2>
                <p class="text-gray-600">This report details the US position data captured for {report_date}.</p>
                <p class="text-gray-600 mt-2">Last updated by <span class="font-semibold">{last_updated_by}</span> at <span class="font-semibold">{last_updated_at}</span>.</p>
            </div>

            <!-- Snapshot Table -->
            <div class="p-8">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">🕒 Snapshot Data</h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full bg-white border border-gray-300">
                        <thead class="bg-gray-100">
                            <tr>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">OMS</th>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Live Sheet</th>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">IB</th>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Margin ($)</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200">
    """

    field_order = ["CE SELL", "PE SELL", "CE BUY", "PE BUY"]

    for time_slot in sorted_times:
        time_data = grouped_by_time[time_slot]
        html_content += f"""
                            <tr>
                                <td class="px-4 py-2 text-sm font-semibold text-gray-900">{time_slot}</td>
        """
        for section in ["OMS", "Live Sheet", "IB"]:
            html_content += f"""
                                <td class="px-4 py-2 text-sm text-gray-700">
                                    <div class="grid grid-cols-2 gap-1">
            """
            for field in field_order:
                item = time_data[section].get(field, {"value": "", "username": "N/A", "filled_at": "N/A"})
                # MODIFIED: Enhanced tooltip text
                tooltip_text = f"Filled by {item['username']} at {item['filled_at']}" if item['username'] != "N/A" else "Not filled"
                html_content += f"""
                                        <div class="flex items-center tooltip">
                                            <span class="font-medium mr-1">{field}:</span>
                                            <span>{item['value']}</span>
                                            <span class="tooltiptext">{tooltip_text}</span>
                                        </div>
                """
            html_content += f"""
                                    </div>
                                </td>
            """
        
        margin_item = time_data["Margin"]
        # MODIFIED: Enhanced tooltip text for margin
        margin_tooltip_text = f"Filled by {margin_item['username']} at {margin_item['filled_at']}" if margin_item['username'] != "N/A" else "Not filled"
        html_content += f"""
                                <td class="px-4 py-2 text-sm text-gray-700 tooltip">
                                    {margin_item['value']}
                                    <span class="tooltiptext">{margin_tooltip_text}</span>
                                </td>
                            </tr>
        """

    html_content += f"""
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Notes -->
            <div class="p-8 border-t border-gray-200">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">📝 Notes / Incident Log</h2>
                <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <p class="text-gray-700 whitespace-pre-wrap">{notes if notes else "No notes recorded."}</p>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="p-6 bg-gray-800 text-white text-center">
                <p class="text-sm">
                    🔒 This report contains sensitive position data.
                </p>
                <p class="text-xs text-gray-400 mt-2">
                    SOP Tracking System - Confidential Data
                </p>
            </div>
        </div>
        
        <!-- Print Button -->
        <div class="no-print text-center mt-8 mb-4">
            <button onclick="window.print()" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold shadow-lg transition duration-200">
                🖨️ Print This Report
            </button>
        </div>
    </body>
    </html>
    """
    
    return html_content