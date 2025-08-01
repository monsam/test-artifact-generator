from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2
import docx
from PIL import Image
import pytesseract
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import base64

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'docx', 'doc'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""

def extract_text_from_image(file_path):
    """Extract text from image using OCR"""
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return ""

def extract_text_from_file(file_path, file_type):
    """Extract text from different file types"""
    if file_type == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_type == 'docx':
        return extract_text_from_docx(file_path)
    elif file_type == 'doc':
        # For .doc files, try to read as text first, then fallback
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except:
            try:
                return extract_text_from_docx(file_path)
            except Exception as e:
                print(f"Error extracting text from DOC: {e}")
                return "Sample requirements document content for testing purposes."
    elif file_type in ['png', 'jpg', 'jpeg']:
        return extract_text_from_image(file_path)
    else:
        # For txt files, read directly
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return "Sample text content for testing purposes."

def generate_test_cases_with_gemini(requirements_text, ux_mockups_text, templates_text):
    """Generate test cases using Gemini API"""
    try:
        prompt = f"""
        Based on the following information, generate comprehensive test cases:

        REQUIREMENTS:
        {requirements_text}

        UX MOCKUPS:
        {ux_mockups_text}

        TEMPLATES:
        {templates_text}

        Please generate:
        1. Functional test cases
        2. Non-functional test cases (performance, security, usability)
        3. Edge case scenarios
        4. Integration test cases

        Format the output as JSON with the following structure:
        {{
            "test_cases": [
                {{
                    "id": "TC001",
                    "title": "Test case title",
                    "description": "Detailed description",
                    "preconditions": ["List of preconditions"],
                    "test_steps": ["Step 1", "Step 2", "Step 3"],
                    "expected_result": "Expected outcome",
                    "test_type": "functional|non-functional|edge-case|integration",
                    "priority": "high|medium|low",
                    "category": "UI|API|Database|Security|Performance"
                }}
            ]
        }}
        """

        # Use Gemini API
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text
        # Find JSON in the response (sometimes Gemini adds extra text)
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
        else:
            raise Exception("No valid JSON found in response")

    except Exception as e:
        print(f"Error generating test cases with Gemini: {e}")
        # Return a sample test case if AI fails
        return {
            "test_cases": [
                {
                    "id": "TC001",
                    "title": "Sample Test Case",
                    "description": "This is a sample test case generated when AI is not available",
                    "preconditions": ["System is running", "User is logged in"],
                    "test_steps": ["Step 1: Navigate to the application", "Step 2: Perform the action", "Step 3: Verify the result"],
                    "expected_result": "Expected outcome is achieved",
                    "test_type": "functional",
                    "priority": "medium",
                    "category": "UI"
                }
            ]
        }

def generate_test_plan_with_gemini(requirements_text, test_cases):
    """Generate test plan using Gemini API"""
    try:
        test_cases_text = json.dumps(test_cases, indent=2)
        
        prompt = f"""
        Based on the requirements and test cases, generate a comprehensive test plan:

        REQUIREMENTS:
        {requirements_text}

        TEST CASES:
        {test_cases_text}

        Please generate a test plan with the following structure:
        {{
            "test_plan": {{
                "project_name": "Project Name",
                "version": "1.0",
                "test_scope": "Description of what will be tested",
                "test_objectives": ["Objective 1", "Objective 2"],
                "test_strategy": "Overall testing approach",
                "test_environment": "Required test environment",
                "test_schedule": "Timeline for testing",
                "test_resources": "Required resources and tools",
                "risk_assessment": "Potential risks and mitigation",
                "entry_criteria": ["Criteria 1", "Criteria 2"],
                "exit_criteria": ["Criteria 1", "Criteria 2"],
                "test_phases": [
                    {{
                        "phase": "Unit Testing",
                        "duration": "1 week",
                        "responsible": "Development Team",
                        "deliverables": ["Unit test results"]
                    }}
                ]
            }}
        }}
        """

        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
        else:
            raise Exception("No valid JSON found in response")

    except Exception as e:
        print(f"Error generating test plan with Gemini: {e}")
        return {
            "test_plan": {
                "project_name": "Sample Project",
                "version": "1.0",
                "test_scope": "Sample test scope",
                "test_objectives": ["Objective 1", "Objective 2"],
                "test_strategy": "Sample testing strategy",
                "test_environment": "Sample test environment",
                "test_schedule": "1 week",
                "test_resources": "Sample resources",
                "risk_assessment": "Sample risks",
                "entry_criteria": ["Criteria 1"],
                "exit_criteria": ["Criteria 1"],
                "test_phases": [
                    {
                        "phase": "Unit Testing",
                        "duration": "1 week",
                        "responsible": "Development Team",
                        "deliverables": ["Unit test results"]
                    }
                ]
            }
        }

def generate_test_report_with_gemini(test_cases, test_results):
    """Generate test report using Gemini API"""
    try:
        test_cases_text = json.dumps(test_cases, indent=2)
        test_results_text = json.dumps(test_results, indent=2)
        
        prompt = f"""
        Based on the test cases and results, generate a comprehensive test report:

        TEST CASES:
        {test_cases_text}

        TEST RESULTS:
        {test_results_text}

        Please generate a test report with the following structure:
        {{
            "test_report": {{
                "project_name": "Project Name",
                "report_date": "Current date",
                "test_summary": {{
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 0,
                    "blocked": 0,
                    "pass_rate": "0%"
                }},
                "test_results": [
                    {{
                        "test_case_id": "TC001",
                        "status": "passed|failed|blocked",
                        "execution_time": "00:05:30",
                        "defects_found": ["Defect 1", "Defect 2"],
                        "notes": "Additional notes"
                    }}
                ],
                "defects_summary": {{
                    "total_defects": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }},
                "recommendations": ["Recommendation 1", "Recommendation 2"],
                "next_steps": ["Step 1", "Step 2"]
            }}
        }}
        """

        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
        else:
            raise Exception("No valid JSON found in response")

    except Exception as e:
        print(f"Error generating test report with Gemini: {e}")
        return {
            "test_report": {
                "project_name": "Sample Project",
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "test_summary": {
                    "total_tests": len(test_cases.get('test_cases', [])),
                    "passed": len(test_cases.get('test_cases', [])) * 0.8,
                    "failed": len(test_cases.get('test_cases', [])) * 0.15,
                    "blocked": len(test_cases.get('test_cases', [])) * 0.05,
                    "pass_rate": "80%"
                },
                "test_results": [],
                "defects_summary": {
                    "total_defects": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                },
                "recommendations": ["Sample recommendation"],
                "next_steps": ["Sample next step"]
            }
        }

def create_pdf_report(data, report_type):
    """Create PDF report from data"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1
    )
    story.append(Paragraph(f"{report_type.upper()} REPORT", title_style))
    story.append(Spacer(1, 12))

    if report_type == "test_cases":
        story.extend(create_test_cases_pdf(data, styles))
    elif report_type == "test_plan":
        story.extend(create_test_plan_pdf(data, styles))
    elif report_type == "test_report":
        story.extend(create_test_report_pdf(data, styles))

    doc.build(story)
    buffer.seek(0)
    return buffer

def create_test_cases_pdf(data, styles):
    """Create test cases PDF content"""
    story = []
    
    for test_case in data.get('test_cases', []):
        # Test Case Header
        story.append(Paragraph(f"Test Case ID: {test_case.get('id', 'N/A')}", styles['Heading2']))
        story.append(Paragraph(f"Title: {test_case.get('title', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Description: {test_case.get('description', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Type: {test_case.get('test_type', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Priority: {test_case.get('priority', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Category: {test_case.get('category', 'N/A')}", styles['Normal']))
        
        # Preconditions
        if test_case.get('preconditions'):
            story.append(Paragraph("Preconditions:", styles['Heading3']))
            for precond in test_case['preconditions']:
                story.append(Paragraph(f"• {precond}", styles['Normal']))
        
        # Test Steps
        if test_case.get('test_steps'):
            story.append(Paragraph("Test Steps:", styles['Heading3']))
            for i, step in enumerate(test_case['test_steps'], 1):
                story.append(Paragraph(f"{i}. {step}", styles['Normal']))
        
        # Expected Result
        story.append(Paragraph(f"Expected Result: {test_case.get('expected_result', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 20))
    
    return story

def create_test_plan_pdf(data, styles):
    """Create test plan PDF content"""
    story = []
    test_plan = data.get('test_plan', {})
    
    # Project Information
    story.append(Paragraph(f"Project Name: {test_plan.get('project_name', 'N/A')}", styles['Heading2']))
    story.append(Paragraph(f"Version: {test_plan.get('version', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Test Scope
    story.append(Paragraph("Test Scope:", styles['Heading3']))
    story.append(Paragraph(test_plan.get('test_scope', 'N/A'), styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Test Objectives
    if test_plan.get('test_objectives'):
        story.append(Paragraph("Test Objectives:", styles['Heading3']))
        for objective in test_plan['test_objectives']:
            story.append(Paragraph(f"• {objective}", styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Test Strategy
    story.append(Paragraph("Test Strategy:", styles['Heading3']))
    story.append(Paragraph(test_plan.get('test_strategy', 'N/A'), styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Test Environment
    story.append(Paragraph("Test Environment:", styles['Heading3']))
    story.append(Paragraph(test_plan.get('test_environment', 'N/A'), styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Test Schedule
    story.append(Paragraph("Test Schedule:", styles['Heading3']))
    story.append(Paragraph(test_plan.get('test_schedule', 'N/A'), styles['Normal']))
    
    return story

def create_test_report_pdf(data, styles):
    """Create test report PDF content"""
    story = []
    test_report = data.get('test_report', {})
    
    # Project Information
    story.append(Paragraph(f"Project Name: {test_report.get('project_name', 'N/A')}", styles['Heading2']))
    story.append(Paragraph(f"Report Date: {test_report.get('report_date', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Test Summary
    summary = test_report.get('test_summary', {})
    story.append(Paragraph("Test Summary:", styles['Heading3']))
    story.append(Paragraph(f"Total Tests: {summary.get('total_tests', 0)}", styles['Normal']))
    story.append(Paragraph(f"Passed: {summary.get('passed', 0)}", styles['Normal']))
    story.append(Paragraph(f"Failed: {summary.get('failed', 0)}", styles['Normal']))
    story.append(Paragraph(f"Blocked: {summary.get('blocked', 0)}", styles['Normal']))
    story.append(Paragraph(f"Pass Rate: {summary.get('pass_rate', '0%')}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Defects Summary
    defects = test_report.get('defects_summary', {})
    story.append(Paragraph("Defects Summary:", styles['Heading3']))
    story.append(Paragraph(f"Total Defects: {defects.get('total_defects', 0)}", styles['Normal']))
    story.append(Paragraph(f"Critical: {defects.get('critical', 0)}", styles['Normal']))
    story.append(Paragraph(f"High: {defects.get('high', 0)}", styles['Normal']))
    story.append(Paragraph(f"Medium: {defects.get('medium', 0)}", styles['Normal']))
    story.append(Paragraph(f"Low: {defects.get('low', 0)}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Recommendations
    if test_report.get('recommendations'):
        story.append(Paragraph("Recommendations:", styles['Heading3']))
        for rec in test_report['recommendations']:
            story.append(Paragraph(f"• {rec}", styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Next Steps
    if test_report.get('next_steps'):
        story.append(Paragraph("Next Steps:", styles['Heading3']))
        for step in test_report['next_steps']:
            story.append(Paragraph(f"• {step}", styles['Normal']))
    
    return story

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads and process them"""
    try:
        if 'requirements' not in request.files or 'ux_mockups' not in request.files or 'templates' not in request.files:
            return jsonify({'error': 'Missing required files'}), 400
        
        requirements_file = request.files['requirements']
        ux_mockups_file = request.files['ux_mockups']
        templates_file = request.files['templates']
        
        # Validate files
        if requirements_file.filename == '' or ux_mockups_file.filename == '' or templates_file.filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        if not all(allowed_file(f.filename) for f in [requirements_file, ux_mockups_file, templates_file]):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save files
        session_id = str(uuid.uuid4())
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        os.makedirs(session_folder, exist_ok=True)
        
        requirements_path = os.path.join(session_folder, secure_filename(requirements_file.filename))
        ux_mockups_path = os.path.join(session_folder, secure_filename(ux_mockups_file.filename))
        templates_path = os.path.join(session_folder, secure_filename(templates_file.filename))
        
        requirements_file.save(requirements_path)
        ux_mockups_file.save(ux_mockups_path)
        templates_file.save(templates_path)
        
        # Extract text from files
        requirements_ext = requirements_file.filename.rsplit('.', 1)[1].lower()
        ux_mockups_ext = ux_mockups_file.filename.rsplit('.', 1)[1].lower()
        templates_ext = templates_file.filename.rsplit('.', 1)[1].lower()
        
        requirements_text = extract_text_from_file(requirements_path, requirements_ext)
        ux_mockups_text = extract_text_from_file(ux_mockups_path, ux_mockups_ext)
        templates_text = extract_text_from_file(templates_path, templates_ext)
        
        # Generate test artifacts
        test_cases = generate_test_cases_with_gemini(requirements_text, ux_mockups_text, templates_text)
        test_plan = generate_test_plan_with_gemini(requirements_text, test_cases)
        
        # Mock test results for demo
        test_results = {
            "executed_tests": len(test_cases.get('test_cases', [])),
            "passed": len(test_cases.get('test_cases', [])) * 0.8,
            "failed": len(test_cases.get('test_cases', [])) * 0.15,
            "blocked": len(test_cases.get('test_cases', [])) * 0.05
        }
        
        test_report = generate_test_report_with_gemini(test_cases, test_results)
        
        # Save results
        results = {
            'session_id': session_id,
            'test_cases': test_cases,
            'test_plan': test_plan,
            'test_report': test_report,
            'timestamp': datetime.now().isoformat()
        }
        
        results_path = os.path.join(session_folder, 'results.json')
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'test_cases_count': len(test_cases.get('test_cases', [])),
            'message': 'Files processed successfully'
        })
        
    except Exception as e:
        print(f"Error processing files: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<session_id>/<artifact_type>')
def download_artifact(session_id, artifact_type):
    """Download generated artifacts as PDF"""
    try:
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        results_path = os.path.join(session_folder, 'results.json')
        
        if not os.path.exists(results_path):
            return jsonify({'error': 'Session not found'}), 404
        
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        if artifact_type not in ['test_cases', 'test_plan', 'test_report']:
            return jsonify({'error': 'Invalid artifact type'}), 400
        
        # Get the specific data for the artifact type
        if artifact_type == 'test_cases':
            data = results.get('test_cases', {})
        elif artifact_type == 'test_plan':
            data = results.get('test_plan', {})
        elif artifact_type == 'test_report':
            data = results.get('test_report', {})
        else:
            data = results
        
        # Create PDF
        pdf_buffer = create_pdf_report(data, artifact_type)
        
        # Save PDF
        output_filename = f"{artifact_type}_{session_id}.pdf"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error downloading artifact: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/results/<session_id>')
def get_results(session_id):
    """Get processing results for a session"""
    try:
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        results_path = os.path.join(session_folder, 'results.json')
        
        if not os.path.exists(results_path):
            return jsonify({'error': 'Session not found'}), 404
        
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error getting results: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 