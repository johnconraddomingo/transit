import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from visualisation.render import generate_dashboard

if __name__ == "__main__":
    print("Starting dashboard generation...")
    generate_dashboard()
    print("Done!")