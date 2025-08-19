#!/usr/bin/env python3
"""
MONGODB PROCESSING PIPELINE

Master script that runs the complete MongoDB-based Wikibase processing pipeline.
This replaces the slow 9-day Wikibase API approach with fast bulk operations.

Pipeline Steps:
1. Import all XML files to MongoDB (minutes)
2. Bulk fix all properties (minutes)  
3. Generate merge mapping CSV (minutes)
4. Export back to XML format (minutes)

Total time: ~30-60 minutes instead of 9+ days
"""

import os
import time
import subprocess
import sys

class MongoDBPipeline:
    def __init__(self):
        self.start_time = time.time()
        self.steps = []
        
    def log_step(self, step_name, duration):
        """Log completed step"""
        self.steps.append((step_name, duration))
        total_time = time.time() - self.start_time
        print(f"OK {step_name}: {duration:.1f}s (Total: {total_time:.1f}s)")
        print("-" * 50)
    
    def run_script(self, script_name, args=None):
        """Run a Python script and return duration"""
        step_start = time.time()
        
        # Ensure we're in the gedcom_tools directory
        script_path = os.path.join("gedcom_tools", script_name)
        cmd = [sys.executable, script_path]
        if args:
            cmd.extend(args)
            
        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
            
            duration = time.time() - step_start
            return duration, True
            
        except subprocess.CalledProcessError as e:
            print(f"Error running {script_name}: {e}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            
            duration = time.time() - step_start
            return duration, False
    
    def check_mongodb_connection(self):
        """Check if MongoDB is available"""
        try:
            import pymongo
            client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
            client.server_info()
            client.close()
            print("OK MongoDB connection successful")
            return True
        except Exception as e:
            print(f"ERROR MongoDB connection failed: {e}")
            print("Please ensure MongoDB is running on localhost:27017")
            return False
    
    def check_xml_files(self):
        """Check if XML files exist"""
        xml_dir = "xml_imports"
        if not os.path.exists(xml_dir):
            print(f"ERROR XML imports directory not found: {xml_dir}")
            return False
            
        xml_files = [f for f in os.listdir(xml_dir) if f.endswith('.xml')]
        if not xml_files:
            print(f"ERROR No XML files found in {xml_dir}")
            return False
            
        print(f"OK Found {len(xml_files)} XML files in {xml_dir}")
        return True
    
    def install_dependencies(self):
        """Install required Python packages"""
        print("Checking dependencies...")
        
        required_packages = [
            'pymongo',
            'python-Levenshtein'
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"OK {package} available")
            except ImportError:
                print(f"Installing {package}...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
    
    def run_full_pipeline(self):
        """Run the complete MongoDB processing pipeline"""
        print("MONGODB WIKIBASE PROCESSING PIPELINE")
        print("=" * 50)
        print("This will process 560MB of data in ~30-60 minutes")
        print("instead of the 9+ days required by the Wikibase API approach.")
        print("=" * 50)
        
        # Prerequisites
        print("\n1. CHECKING PREREQUISITES")
        print("-" * 30)
        
        if not self.check_mongodb_connection():
            return False
            
        if not self.check_xml_files():
            return False
            
        try:
            self.install_dependencies()
        except Exception as e:
            print(f"ERROR Failed to install dependencies: {e}")
            return False
        
        # Step 1: Import XML files to MongoDB
        print("\n2. IMPORTING XML FILES TO MONGODB")
        print("-" * 40)
        duration, success = self.run_script("mongodb_xml_importer.py")
        if not success:
            print("ERROR XML import failed")
            return False
        self.log_step("XML Import", duration)
        
        # Step 2: Bulk property fixes
        print("\n3. BULK PROPERTY FIXES")
        print("-" * 25)
        duration, success = self.run_script("mongodb_bulk_processor.py")
        if not success:
            print("ERROR Bulk processing failed")
            return False
        self.log_step("Bulk Processing", duration)
        
        # Step 3: Generate merge mapping
        print("\n4. GENERATING MERGE MAPPING")
        print("-" * 30)
        duration, success = self.run_script("mongodb_merge_mapper.py")
        if not success:
            print("ERROR Merge mapping failed")
            return False
        self.log_step("Merge Mapping", duration)
        
        # Step 4: Export to XML
        print("\n5. EXPORTING TO XML")
        print("-" * 20)
        duration, success = self.run_script("mongodb_to_xml_exporter.py", ["--split"])
        if not success:
            print("ERROR XML export failed")
            return False
        self.log_step("XML Export", duration)
        
        # Summary
        total_time = time.time() - self.start_time
        print("\n" + "=" * 50)
        print("PIPELINE COMPLETE!")
        print("=" * 50)
        
        for step_name, step_duration in self.steps:
            print(f"{step_name}: {step_duration:.1f}s")
        
        print(f"\nTotal Time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        print(f"Compared to 9+ days (777,600+ seconds), this is {777600/total_time:.0f}x faster!")
        
        print("\nOutput Files Generated:")
        print("- mongodb_correspondence.csv (entity correspondence)")
        print("- merge_mapping.csv (duplicate merge candidates)")
        print("- processed_xml/ (clean XML exports for import)")
        
        return True
    
    def run_individual_step(self, step):
        """Run an individual pipeline step"""
        if step == "import":
            print("Running XML import...")
            duration, success = self.run_script("mongodb_xml_importer.py")
            self.log_step("XML Import", duration)
            
        elif step == "process":
            print("Running bulk processing...")
            duration, success = self.run_script("mongodb_bulk_processor.py")
            self.log_step("Bulk Processing", duration)
            
        elif step == "merge":
            print("Running merge mapping...")
            duration, success = self.run_script("mongodb_merge_mapper.py")
            self.log_step("Merge Mapping", duration)
            
        elif step == "export":
            print("Running XML export...")
            duration, success = self.run_script("mongodb_to_xml_exporter.py", ["--split"])
            self.log_step("XML Export", duration)
            
        else:
            print(f"Unknown step: {step}")
            print("Available steps: import, process, merge, export")
            return False
            
        return success

def main():
    pipeline = MongoDBPipeline()
    
    if len(sys.argv) > 1:
        # Run individual step
        step = sys.argv[1]
        pipeline.run_individual_step(step)
    else:
        # Run full pipeline
        pipeline.run_full_pipeline()

if __name__ == "__main__":
    main()