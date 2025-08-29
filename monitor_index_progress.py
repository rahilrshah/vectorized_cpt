import time
import datetime
from firebase_utils import init_firestore
from config import cred_path, collection_name

def test_index_readiness():
    """Test if the vector index is ready by attempting a simple vector query"""
    try:
        db = init_firestore(cred_path)
        if not db:
            return False, "Failed to connect to Firestore"
        
        # Get a sample vector
        sample_docs = list(db.collection(collection_name).limit(1).stream())
        if not sample_docs:
            return False, "No documents found"
            
        sample_data = sample_docs[0].to_dict()
        if 'vector' not in sample_data:
            return False, "No vector field found"
            
        sample_vector = sample_data['vector']
        
        # Try a vector query - this will fail if index is still building
        vector_query = db.collection(collection_name).findNearest(
            "vector", 
            sample_vector, 
            {"limit": 2, "distanceMeasure": "COSINE"}
        )
        
        results = vector_query.get()
        return True, f"SUCCESS! Index ready, returned {len(results.docs)} results"
        
    except AttributeError:
        # Local environment doesn't have findNearest - use alternative check
        return "unknown", "Local environment can't test vector queries directly"
    except Exception as e:
        error_msg = str(e)
        if "index is currently building" in error_msg.lower():
            return False, "Index still building"
        elif "failed_precondition" in error_msg.lower():
            return False, "Index still building (FAILED_PRECONDITION)"
        else:
            return False, f"Other error: {error_msg[:100]}..."

def check_cloud_function_logs():
    """Check recent Cloud Function logs for index status"""
    try:
        import subprocess
        
        # Get the most recent logs
        result = subprocess.run(
            ["firebase", "functions:log", "--only", "findSimilarCptCodes", "--lines", "10"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logs = result.stdout
            
            # Look for recent errors or successes
            lines = logs.split('\n')
            recent_logs = []
            
            for line in lines[-20:]:  # Last 20 lines
                if any(keyword in line.lower() for keyword in [
                    'index', 'building', 'failed_precondition', 'firestore query returned', 'success'
                ]):
                    # Extract timestamp and message
                    if 'Z' in line:
                        parts = line.split(' ', 2)
                        if len(parts) >= 3:
                            timestamp = parts[0]
                            message = parts[2]
                            recent_logs.append((timestamp, message))
            
            return recent_logs
        else:
            return [("ERROR", f"Failed to get logs: {result.stderr}")]
            
    except Exception as e:
        return [("ERROR", f"Exception getting logs: {e}")]

def monitor_index_progress():
    """Monitor the index building progress with real-time updates"""
    print("="*80)
    print("🔍 FIRESTORE VECTOR INDEX PROGRESS MONITOR")
    print("="*80)
    
    start_time = datetime.datetime.now()
    check_count = 0
    
    print(f"Started monitoring at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Collection: {collection_name}")
    print(f"Checking every 30 seconds...")
    print("-"*80)
    
    while True:
        check_count += 1
        current_time = datetime.datetime.now()
        elapsed = current_time - start_time
        
        print(f"\n📊 CHECK #{check_count} - {current_time.strftime('%H:%M:%S')} (elapsed: {elapsed})")
        
        # Test 1: Direct index test (local)
        print("   🧪 Testing local vector query capability...")
        index_ready, message = test_index_readiness()
        
        if index_ready == True:
            print(f"   ✅ LOCAL TEST: {message}")
            print("\n🎉 INDEX IS READY! Testing the website now should work!")
            break
        elif index_ready == False:
            print(f"   ⏳ LOCAL TEST: {message}")
        else:
            print(f"   ℹ️  LOCAL TEST: {message}")
        
        # Test 2: Check Cloud Function logs
        print("   📋 Checking recent Cloud Function activity...")
        recent_logs = check_cloud_function_logs()
        
        if recent_logs:
            latest_relevant = recent_logs[-3:]  # Show last 3 relevant entries
            for timestamp, message in latest_relevant:
                # Format timestamp
                try:
                    if timestamp.endswith('Z') and 'T' in timestamp:
                        dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%H:%M:%S')
                    else:
                        time_str = timestamp[:8] if len(timestamp) > 8 else timestamp
                except:
                    time_str = timestamp[:10]
                
                # Determine status icon
                if 'building' in message.lower() or 'failed_precondition' in message.lower():
                    icon = "⏳"
                elif 'firestore query returned' in message.lower():
                    icon = "✅"
                elif 'error' in message.lower():
                    icon = "❌"
                else:
                    icon = "ℹ️ "
                
                print(f"   {icon} {time_str}: {message[:80]}...")
                
                # Check if we found success in logs
                if 'firestore query returned' in message.lower() and 'documents' in message.lower():
                    print(f"\n🎉 SUCCESS DETECTED IN LOGS! Index appears ready!")
                    return
        else:
            print("   ℹ️  No recent relevant log entries found")
        
        # Test 3: Time-based estimation
        print("   ⏰ Time-based estimation...")
        
        # Estimate based on typical index building times
        minutes_elapsed = elapsed.total_seconds() / 60
        
        if minutes_elapsed < 30:
            progress_estimate = f"{minutes_elapsed:.0f}/30+ min (early stage)"
        elif minutes_elapsed < 60:
            progress_estimate = f"{minutes_elapsed:.0f}/60+ min (likely still building)"
        elif minutes_elapsed < 120:
            progress_estimate = f"{minutes_elapsed:.0f}/120 min (should complete soon)"
        else:
            progress_estimate = f"{minutes_elapsed:.0f} min (should be done - may be an issue)"
        
        print(f"   📈 Progress estimate: {progress_estimate}")
        
        # Wait before next check
        if check_count == 1:
            print(f"\n   ⏸️  Waiting 30 seconds before next check... (Press Ctrl+C to stop)")
        
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitoring stopped by user after {check_count} checks")
            break
        
        # Add some spacing
        print("-"*60)
    
    final_time = datetime.datetime.now()
    total_elapsed = final_time - start_time
    print(f"\n📋 MONITORING SUMMARY:")
    print(f"   Total monitoring time: {total_elapsed}")
    print(f"   Total checks performed: {check_count}")
    print(f"   Final status: {'INDEX READY' if index_ready == True else 'Still building or unknown'}")

def quick_status_check():
    """Quick one-time status check without continuous monitoring"""
    print("🔍 QUICK INDEX STATUS CHECK")
    print("="*50)
    
    # Check current time
    current_time = datetime.datetime.now()
    print(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test index
    index_ready, message = test_index_readiness()
    print(f"Index status: {message}")
    
    # Check recent logs
    print("\nRecent Cloud Function activity:")
    recent_logs = check_cloud_function_logs()
    
    if recent_logs:
        for timestamp, message in recent_logs[-2:]:  # Show last 2
            try:
                if timestamp.endswith('Z') and 'T' in timestamp:
                    dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                else:
                    time_str = timestamp
            except:
                time_str = timestamp[:10]
            
            print(f"  {time_str}: {message[:60]}...")
    
    if index_ready == True:
        print(f"\n✅ INDEX IS READY!")
    else:
        print(f"\n⏳ Index still building. Try again in 10-20 minutes.")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'quick':
        quick_status_check()
    else:
        print("Starting continuous monitoring...")
        print("(Use 'python3 monitor_index_progress.py quick' for a one-time check)")
        print()
        monitor_index_progress()