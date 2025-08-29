#!/usr/bin/env python3
"""
Garmin Connect Data Exporter for LLM Analysis
Exports all available Garmin Connect data into a single structured JSON file
optimized for analysis by Large Language Models.

Requirements:
pip install garminconnect pandas

Usage:
python garmin_llm_exporter.py
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from garminconnect import Garmin
import getpass

class GarminLLMExporter:
    def __init__(self, email=None, password=None):
        """Initialize Garmin Connect exporter for LLM analysis."""
        self.email = email
        self.password = password
        self.client = None
        self.token_store = os.path.expanduser("~/.garminconnect")
        self.api_methods = {}
        
    def authenticate(self):
        """Authenticate with Garmin Connect."""
        try:
            self.client = Garmin()
            self.client.login(self.token_store)
            print("✅ Authentication successful (stored tokens)")
            self._discover_api_methods()
            return True
        except:
            if not self.email:
                self.email = input("Garmin Connect email: ")
            if not self.password:
                self.password = getpass.getpass("Password: ")
            
            try:
                self.client = Garmin(self.email, self.password)
                self.client.login()
                print("✅ Authentication successful (credentials)")
                self._discover_api_methods()
                return True
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                return False

    def _discover_api_methods(self):
        """Discover available API methods to avoid errors."""
        methods_to_check = [
            'get_daily_steps', 'get_body_battery', 'get_floors', 'get_weigh_ins',
            'get_menstrual_calendar_data', 'get_pregnancy_summary', 'get_steps_data',
            'get_stress_data', 'get_heart_rates', 'get_sleep_data', 'get_hydration_data',
            'get_respiration_data', 'get_pulse_ox', 'get_training_readiness',
            'get_training_status', 'get_rhr_day', 'get_body_composition'
        ]
        
        for method in methods_to_check:
            self.api_methods[method] = hasattr(self.client, method)
            
        available = sum(self.api_methods.values())
        print(f"🔍 Discovered {available}/{len(methods_to_check)} available API methods")

    def safe_call(self, func, *args, **kwargs):
        """Safely call API method with error handling."""
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            method_name = getattr(func, '__name__', 'unknown_method')
            if "400" in str(e):
                print(f"⚠️ {method_name}: Bad request format (skipping)")
            elif "404" in str(e):
                print(f"⚠️ {method_name}: Data not found")
            elif "arguments" in str(e):
                print(f"⚠️ {method_name}: Invalid parameters")
            else:
                print(f"⚠️ {method_name}: {str(e)[:80]}...")
            return None

    def export_user_profile(self):
        """Export user profile and device information."""
        print("👤 Exporting user profile...")
        
        today = datetime.now().date().isoformat()
        
        profile = {
            "full_name": self.safe_call(self.client.get_full_name),
            "unit_system": self.safe_call(self.client.get_unit_system),
            "user_summary": self.safe_call(self.client.get_user_summary, today),
            "devices": self.safe_call(self.client.get_devices)
        }
        
        return {"user_profile": profile}

    def export_activities(self, limit=200):
        """Export activity data with smart sampling."""
        print("🏃 Exporting activities...")
        
        activities_list = self.safe_call(self.client.get_activities, 0, limit)
        last_activity = self.safe_call(self.client.get_last_activity)
        
        # Get detailed data for first 5 activities to save time
        detailed_activities = []
        if activities_list:
            for i, activity in enumerate(activities_list[:5]):
                print(f"📊 Getting activity details {i+1}/5")
                activity_id = activity.get('activityId')
                if activity_id:
                    details = self.safe_call(self.client.get_activity, activity_id)
                    if details:
                        detailed_activities.append(details)
        
        return {
            "activities": {
                "metadata": {
                    "total_requested": limit,
                    "actual_count": len(activities_list) if activities_list else 0,
                    "detailed_sample": len(detailed_activities)
                },
                "all_activities": activities_list,
                "last_activity": last_activity,
                "detailed_sample": detailed_activities
            }
        }

    def export_daily_health_metrics(self, days_back=14):
        """Export daily health metrics with smart sampling."""
        print(f"💓 Exporting health metrics for {days_back} days...")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        health_data = {
            "daily_health_metrics": {
                "metadata": {
                    "period_start": start_date.isoformat(),
                    "period_end": end_date.isoformat(),
                    "sampling_strategy": "every_2nd_day"
                },
                "daily_summaries": [],
                "heart_rate_data": [],
                "sleep_data": [],
                "stress_data": [],
                "steps_data": [],
                "body_battery_indicators": []
            }
        }
        
        # Process every 2nd day to balance detail with file size
        current = start_date
        day_counter = 0
        
        while current <= end_date:
            if day_counter % 2 == 0:
                date_str = current.isoformat()
                print(f"📅 Processing {date_str}")
                
                # Main daily summary
                summary = self.safe_call(self.client.get_stats_and_body, date_str)
                if summary:
                    health_data["daily_health_metrics"]["daily_summaries"].append({
                        "date": date_str, "data": summary
                    })
                    
                    # Extract Body Battery from summary if available
                    summary_str = str(summary)
                    if 'bodyBattery' in summary_str or 'bodyBatteryValuesArray' in summary_str:
                        health_data["daily_health_metrics"]["body_battery_indicators"].append({
                            "date": date_str, "found_in_summary": True
                        })
                
                # Heart rate data
                if self.api_methods.get('get_heart_rates', False):
                    hr = self.safe_call(self.client.get_heart_rates, date_str)
                    if hr:
                        health_data["daily_health_metrics"]["heart_rate_data"].append({
                            "date": date_str, "data": hr
                        })
                
                # Sleep data
                if self.api_methods.get('get_sleep_data', False):
                    sleep = self.safe_call(self.client.get_sleep_data, date_str)
                    if sleep:
                        health_data["daily_health_metrics"]["sleep_data"].append({
                            "date": date_str, "data": sleep
                        })
                
                # Stress data
                if self.api_methods.get('get_stress_data', False):
                    stress = self.safe_call(self.client.get_stress_data, date_str)
                    if stress:
                        health_data["daily_health_metrics"]["stress_data"].append({
                            "date": date_str, "data": stress
                        })
                
                # Steps data (using correct method)
                if self.api_methods.get('get_steps_data', False):
                    steps = self.safe_call(self.client.get_steps_data, date_str)
                    if steps:
                        health_data["daily_health_metrics"]["steps_data"].append({
                            "date": date_str, "data": steps
                        })
            
            current += timedelta(days=1)
            day_counter += 1
        
        return health_data

    def export_fitness_metrics(self, days_back=30):
        """Export fitness and training metrics."""
        print("🏋️ Exporting fitness metrics...")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        fitness_data = {
            "fitness_metrics": {
                "metadata": {
                    "period_start": start_date.isoformat(),
                    "period_end": end_date.isoformat(),
                    "sampling_strategy": "weekly"
                },
                "training_readiness": [],
                "training_status": [],
                "resting_heart_rate": [],
                "body_composition": [],
                "weight_measurements": None
            }
        }
        
        # Check weekly to reduce API calls
        current = start_date
        while current <= end_date:
            date_str = current.isoformat()
            
            # Training readiness
            if self.api_methods.get('get_training_readiness', False):
                readiness = self.safe_call(self.client.get_training_readiness, date_str)
                if readiness:
                    fitness_data["fitness_metrics"]["training_readiness"].append({
                        "date": date_str, "data": readiness
                    })
            
            # Training status
            if self.api_methods.get('get_training_status', False):
                status = self.safe_call(self.client.get_training_status, date_str)
                if status:
                    fitness_data["fitness_metrics"]["training_status"].append({
                        "date": date_str, "data": status
                    })
            
            # Resting heart rate
            if self.api_methods.get('get_rhr_day', False):
                rhr = self.safe_call(self.client.get_rhr_day, date_str)
                if rhr:
                    fitness_data["fitness_metrics"]["resting_heart_rate"].append({
                        "date": date_str, "data": rhr
                    })
            
            # Body composition
            if self.api_methods.get('get_body_composition', False):
                body_comp = self.safe_call(self.client.get_body_composition, date_str)
                if body_comp:
                    fitness_data["fitness_metrics"]["body_composition"].append({
                        "date": date_str, "data": body_comp
                    })
            
            current += timedelta(days=7)  # Weekly sampling
        
        # Weight measurements (if available)
        if self.api_methods.get('get_weigh_ins', False):
            try:
                weight_data = self.safe_call(self.client.get_weigh_ins, 
                                           start_date.isoformat(),
                                           end_date.isoformat())
                fitness_data["fitness_metrics"]["weight_measurements"] = weight_data
            except:
                pass
        
        return fitness_data

    def export_specialized_health(self, days_back=21):
        """Export specialized health metrics."""
        print("🫁 Exporting specialized health metrics...")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        specialized = {
            "specialized_health": {
                "metadata": {
                    "period_start": start_date.isoformat(),
                    "period_end": end_date.isoformat(),
                    "sampling_strategy": "weekly"
                },
                "respiration_data": [],
                "pulse_ox_data": [],
                "hydration_data": [],
                "womens_health": {}
            }
        }
        
        # Weekly sampling for specialized metrics
        current = start_date
        while current <= end_date:
            date_str = current.isoformat()
            
            # Respiration data
            if self.api_methods.get('get_respiration_data', False):
                resp = self.safe_call(self.client.get_respiration_data, date_str)
                if resp:
                    specialized["specialized_health"]["respiration_data"].append({
                        "date": date_str, "data": resp
                    })
            
            # Pulse oximetry
            if self.api_methods.get('get_pulse_ox', False):
                pulse_ox = self.safe_call(self.client.get_pulse_ox, date_str)
                if pulse_ox:
                    specialized["specialized_health"]["pulse_ox_data"].append({
                        "date": date_str, "data": pulse_ox
                    })
            
            # Hydration
            if self.api_methods.get('get_hydration_data', False):
                hydration = self.safe_call(self.client.get_hydration_data, date_str)
                if hydration:
                    specialized["specialized_health"]["hydration_data"].append({
                        "date": date_str, "data": hydration
                    })
            
            current += timedelta(days=7)
        
        # Women's health data (full period)
        if self.api_methods.get('get_menstrual_calendar_data', False):
            menstrual = self.safe_call(self.client.get_menstrual_calendar_data,
                                     start_date.isoformat(), end_date.isoformat())
            specialized["specialized_health"]["womens_health"]["menstrual"] = menstrual
        
        if self.api_methods.get('get_pregnancy_summary', False):
            pregnancy = self.safe_call(self.client.get_pregnancy_summary)
            specialized["specialized_health"]["womens_health"]["pregnancy"] = pregnancy
        
        return specialized

    def create_llm_analysis_context(self, all_data):
        """Create analysis context and instructions for LLM."""
        
        context = {
            "llm_analysis_context": {
                "export_timestamp": datetime.now().isoformat(),
                "data_overview": {},
                "available_metrics": [],
                "suggested_analyses": [],
                "data_quality_notes": [],
                "analysis_instructions": {
                    "primary_focus": [
                        "Identify patterns in activity and health data",
                        "Analyze correlations between sleep, stress, and performance",
                        "Assess training load and recovery patterns",
                        "Provide actionable health and fitness insights"
                    ],
                    "data_format_notes": [
                        "All dates in YYYY-MM-DD ISO format",
                        "Some metrics sampled (every 2nd/7th day) to optimize file size",
                        "Missing data points are normal - not all metrics available daily",
                        "Look for trends rather than absolute values"
                    ],
                    "recommended_approach": [
                        "Start with data_overview to understand available metrics",
                        "Focus on activities and daily_health_metrics for main insights",
                        "Cross-reference sleep and stress with activity performance",
                        "Provide specific, actionable recommendations"
                    ]
                }
            }
        }
        
        # Analyze available data
        llm_context = context["llm_analysis_context"]
        
        if "activities" in all_data and all_data["activities"].get("all_activities"):
            activities_count = len(all_data["activities"]["all_activities"])
            llm_context["data_overview"]["activities"] = f"{activities_count} activities recorded"
            llm_context["available_metrics"].append("activity_patterns")
            llm_context["suggested_analyses"].append("activity_trends_and_performance_analysis")
        
        if "daily_health_metrics" in all_data:
            health = all_data["daily_health_metrics"]
            if health.get("heart_rate_data"):
                llm_context["available_metrics"].append("heart_rate_data")
                llm_context["suggested_analyses"].append("heart_rate_zone_analysis")
            
            if health.get("sleep_data"):
                llm_context["available_metrics"].append("sleep_patterns")
                llm_context["suggested_analyses"].append("sleep_quality_and_recovery_assessment")
            
            if health.get("stress_data"):
                llm_context["available_metrics"].append("stress_levels")
                llm_context["suggested_analyses"].append("stress_impact_on_performance")
        
        if "fitness_metrics" in all_data:
            fitness = all_data["fitness_metrics"]
            if fitness.get("training_readiness"):
                llm_context["suggested_analyses"].append("training_readiness_optimization")
            if fitness.get("resting_heart_rate"):
                llm_context["suggested_analyses"].append("cardiovascular_fitness_trends")
        
        return context

    def export_complete_dataset(self, days_back=30):
        """
        Export complete Garmin Connect dataset for LLM analysis.
        """
        if not self.authenticate():
            return False

        print(f"\n🚀 Exporting Garmin Connect data for LLM analysis")
        print(f"📅 Time period: {days_back} days")
        print("⚡ Optimized for API stability and LLM processing\n")
        
        try:
            # Collect all data sections
            all_data = {}
            
            # 1. User profile and devices
            all_data.update(self.export_user_profile())
            
            # 2. Activities
            all_data.update(self.export_activities(limit=300))
            
            # 3. Daily health metrics
            all_data.update(self.export_daily_health_metrics(days_back=days_back))
            
            # 4. Fitness metrics
            all_data.update(self.export_fitness_metrics(days_back=days_back))
            
            # 5. Specialized health metrics
            all_data.update(self.export_specialized_health(days_back=days_back))
            
            # 6. LLM analysis context
            all_data.update(self.create_llm_analysis_context(all_data))
            
            # Save to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"garmin_data_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False, default=str)
            
            # File statistics
            file_size = os.path.getsize(filename) / (1024*1024)
            sections_with_data = sum(1 for k, v in all_data.items() if v)
            
            print(f"\n✅ EXPORT COMPLETED!")
            print(f"📁 File: {filename}")
            print(f"💾 Size: {file_size:.1f} MB")
            print(f"📊 Data sections: {sections_with_data}")
            
            print(f"\n📋 EXPORTED DATA SECTIONS:")
            for section_name, section_data in all_data.items():
                status = "✅" if section_data else "⚪"
                print(f"   {status} {section_name}")
            
            print(f"\n🤖 FOR LLM ANALYSIS:")
            print(f"   1. Upload {filename} to your preferred LLM")
            print(f"   2. Start with the 'llm_analysis_context' section")
            print(f"   3. Ask for patterns, insights, and recommendations")
            
            return filename
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return False

def main():
    print("🤖 Garmin Connect → LLM Data Exporter")
    print("=" * 40)
    print("📊 Export all your Garmin data for AI analysis")
    print("🎯 Single file, optimized for LLM processing")
    print("=" * 40)
    
    exporter = GarminLLMExporter()
    
    try:
        days = input("\nDays to export (default 21): ")
        days = int(days) if days.strip() else 21
    except ValueError:
        days = 21
    
    filename = exporter.export_complete_dataset(days_back=days)
    
    if filename:
        print(f"\n🎉 SUCCESS! {filename} is ready for LLM analysis")
        print("\n📤 Next step: Upload to ChatGPT/Claude and ask for insights!")
    else:
        print("\n❌ Export failed")

if __name__ == "__main__":
    main()
    