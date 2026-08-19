import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../worker')))

import diagnostics

def run_smoke_test():
    print("Initiating Fuzz-Sentinel Worker Diagnostics Pre-Flight Check...")
    print("=================================================================")
    
    try:
        diag = diagnostics.get_diagnostics()
        print(json.dumps(diag, indent=2))
        print("=================================================================")
        
        if diag['status'] == 'ERROR':
            print("\n[CRITICAL FAILURE] Worker pre-flight diagnostic failed!")
            for issue in diag['issues']:
                print(f" -> {issue}")
            
            print("\nHALTING OPERATION: Cannot proceed to Fuzzing Campaign execution due to missing dependencies.")
            print("To prevent fabricating campaign metrics, the execution is securely blocked.")
            sys.exit(1)
            
        print("\n[SUCCESS] Environment verified. Proceeding to campaign execution...")
        # Since we are mocking failures properly, this line won't be reached if WinAFL isn't there.
    except Exception as e:
        print(f"\n[FATAL EXCEPTION] Diagnostic routine crashed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_smoke_test()
