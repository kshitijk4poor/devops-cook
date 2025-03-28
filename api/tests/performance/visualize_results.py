#!/usr/bin/env python3

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import glob

def find_latest_results():
    """Find the most recent test results in the results directory."""
    results_dir = Path(__file__).parent / "results"
    
    # Get all CSV files matching the pattern
    stats_files = glob.glob(str(results_dir / "*_stats.csv"))
    
    if not stats_files:
        print("No test result files found.")
        return None
    
    # Sort by modification time to get the most recent
    latest_file = max(stats_files, key=os.path.getmtime)
    
    # Get corresponding request file
    latest_base = os.path.basename(latest_file).replace('_stats.csv', '')
    request_file = os.path.join(os.path.dirname(latest_file), f"{latest_base}_requests.csv")
    
    if not os.path.exists(request_file):
        print(f"Warning: Request file for {latest_file} not found.")
        request_file = None
    
    return latest_file, request_file

def visualize_test_results(stats_file, requests_file=None):
    """Create visualization of test results."""
    # Load test results
    stats_data = pd.read_csv(stats_file)
    
    print(f"Loaded test results from {stats_file}")
    print(f"Test summary: {len(stats_data)} endpoints tested")
    
    # Set up the style for our charts
    sns.set(style="whitegrid")
    
    # Create a directory for the visualizations
    output_dir = Path(stats_file).parent / "visualizations"
    output_dir.mkdir(exist_ok=True)
    
    # 1. Create Response Time by Endpoint chart
    plt.figure(figsize=(12, 8))
    chart = sns.barplot(x="Name", y="Average Response Time", data=stats_data)
    chart.set_xticklabels(chart.get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.title("Average Response Time by Endpoint")
    plt.tight_layout()
    plt.savefig(output_dir / "response_times.png")
    
    # 2. Create success/failure rate chart
    plt.figure(figsize=(12, 8))
    
    # Calculate success rate
    stats_data['Success Count'] = stats_data['Request Count'] - stats_data['Failure Count']
    stats_data['Success Rate'] = stats_data['Success Count'] / stats_data['Request Count'] * 100
    
    # Plot success rate
    chart = sns.barplot(x="Name", y="Success Rate", data=stats_data)
    chart.set_xticklabels(chart.get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.title("Success Rate by Endpoint (%)")
    plt.ylim(0, 100)  # Set y-axis to percentage scale
    plt.tight_layout()
    plt.savefig(output_dir / "success_rate.png")
    
    # 3. Create min/average/max response time comparison chart
    plt.figure(figsize=(12, 8))
    
    # Prepare data in long format for grouped bar chart
    time_data = pd.melt(stats_data, 
                         id_vars=["Name"], 
                         value_vars=["Min Response Time", "Median Response Time", "Average Response Time", "Max Response Time"],
                         var_name="Metric", value_name="Response Time (ms)")
    
    # Plot the comparison
    chart = sns.barplot(x="Name", y="Response Time (ms)", hue="Metric", data=time_data)
    chart.set_xticklabels(chart.get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.title("Response Time Comparison by Endpoint")
    plt.tight_layout()
    plt.savefig(output_dir / "response_time_comparison.png")
    
    # 4. If requests file exists, plot requests over time
    if requests_file and os.path.exists(requests_file):
        requests_data = pd.read_csv(requests_file)
        
        # Convert timestamp to datetime
        requests_data['timestamp'] = pd.to_datetime(requests_data['timestamp'], unit='s')
        
        # Group by timestamp and endpoint to see requests over time
        time_series = requests_data.groupby([pd.Grouper(key='timestamp', freq='1s'), 'name']).size().unstack().fillna(0)
        
        # Plot requests over time
        plt.figure(figsize=(14, 8))
        time_series.plot(ax=plt.gca())
        plt.title("Requests Over Time")
        plt.xlabel("Time")
        plt.ylabel("Number of Requests")
        plt.tight_layout()
        plt.savefig(output_dir / "requests_over_time.png")
        
        # 5. Create response time distribution chart
        plt.figure(figsize=(14, 8))
        successful = requests_data[requests_data['success'] == True]
        
        endpoints = successful['name'].unique()
        for endpoint in endpoints[:5]:  # Limit to first 5 endpoints to avoid overcrowding
            subset = successful[successful['name'] == endpoint]
            sns.histplot(subset['response_time'], kde=True, label=endpoint, alpha=0.6)
            
        plt.title("Response Time Distribution")
        plt.xlabel("Response Time (ms)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "response_time_distribution.png")
    
    print(f"Visualizations created in {output_dir}")
    return output_dir

def main():
    """Main entry point for the script."""
    if len(sys.argv) > 1:
        stats_file = sys.argv[1]
        requests_file = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # Find the latest results
        files = find_latest_results()
        if not files:
            return
        stats_file, requests_file = files
    
    visualize_test_results(stats_file, requests_file)

if __name__ == "__main__":
    main()