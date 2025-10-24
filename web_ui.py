from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict
import csv
import os
from knowledge_manager import (
    get_unanswered_questions,
    get_answered_questions,
    get_knowledge_stats,
    initialize_knowledge_base
)

app = FastAPI(title="Telephony Agent Q&A Manager")

KNOWLEDGE_FILE = "knowledge_base.csv"

class AnswerRequest(BaseModel):
    question: str
    answer: str

class DeleteRequest(BaseModel):
    question: str

class StatsResponse(BaseModel):
    total: int
    answered: int
    unanswered: int

class QuestionItem(BaseModel):
    question: str
    answer: str
    answered: str
    timestamp: str
    caller_phone: str

class AnsweredItem(BaseModel):
    question: str
    answer: str

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telephony Agent Q&A Manager</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 0;
        }

        .top-nav {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 40px;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .nav-content {
            max-width: 1600px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-text h1 {
            font-size: 1.5em;
            font-weight: 700;
            margin: 0;
        }

        .logo-text p {
            font-size: 0.85em;
            opacity: 0.9;
            margin: 0;
        }

        .nav-stats {
            display: flex;
            gap: 30px;
        }

        .nav-stat {
            text-align: center;
        }

        .nav-stat-value {
            font-size: 1.8em;
            font-weight: 700;
            display: block;
        }

        .nav-stat-label {
            font-size: 0.75em;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 30px 40px;
        }

        .main-layout {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        @media (max-width: 1200px) {
            .main-layout {
                grid-template-columns: 1fr;
            }
        }

        .section {
            background: white;
            border-radius: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .section-header {
            background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%);
            padding: 20px 25px;
            border-bottom: 2px solid #667eea;
        }

        .section-title {
            color: #4c1d95;
            font-size: 1.3em;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 0;
        }

        .section-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 700;
            margin-left: auto;
        }

        .section-body {
            padding: 25px;
            max-height: 70vh;
            overflow-y: auto;
        }

        .section-body::-webkit-scrollbar {
            width: 8px;
        }

        .section-body::-webkit-scrollbar-track {
            background: #f1f1f1;
        }

        .section-body::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 4px;
        }

        .section-body::-webkit-scrollbar-thumb:hover {
            background: #764ba2;
        }

        .question-card {
            background: linear-gradient(135deg, #f5f7ff 0%, #faf5ff 100%);
            border: 2px solid #c7d2fe;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }

        .question-card:hover {
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }

        .question-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }

        .question-text {
            color: #1f2937;
            font-size: 1.1em;
            font-weight: 600;
            line-height: 1.5;
            flex: 1;
        }

        .question-meta {
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
            padding: 10px;
            background: white;
            border-radius: 8px;
        }

        .meta-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85em;
            color: #6b7280;
        }

        textarea {
            width: 100%;
            padding: 14px;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-size: 0.95em;
            font-family: inherit;
            resize: vertical;
            min-height: 100px;
            margin-bottom: 12px;
            transition: all 0.3s ease;
            background: white;
        }

        textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .btn-group {
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            font-size: 0.9em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            flex: 1;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }

        .btn-primary:active {
            transform: translateY(0);
        }

        .btn-danger {
            background: #ef4444;
            color: white;
        }

        .btn-danger:hover {
            background: #dc2626;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(239, 68, 68, 0.3);
        }

        .answered-item {
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }

        .answered-item:hover {
            border-color: #10b981;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
        }

        .answered-question {
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 10px;
            display: flex;
            align-items: flex-start;
            gap: 8px;
        }

        .answered-answer {
            color: #6b7280;
            line-height: 1.6;
            padding-left: 24px;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #9ca3af;
        }

        .empty-state-text {
            font-size: 1.1em;
            font-weight: 500;
        }

        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            font-size: 1.4em;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            z-index: 50;
        }

        .refresh-btn:hover {
            transform: scale(1.1) rotate(180deg);
            box-shadow: 0 6px 25px rgba(102, 126, 234, 0.5);
        }

        .notification {
            position: fixed;
            top: 90px;
            right: 30px;
            padding: 16px 24px;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            z-index: 1000;
            animation: slideIn 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .notification.success {
            background: #10b981;
        }

        .notification.error {
            background: #ef4444;
        }

        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #9ca3af;
        }

        .spinner {
            border: 3px solid #f3f4f6;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
            .top-nav {
                padding: 15px 20px;
            }

            .nav-content {
                flex-direction: column;
                gap: 15px;
            }

            .container {
                padding: 20px;
            }

            .btn-group {
                flex-direction: column;
            }

            .btn-danger {
                margin-left: 0;
            }
        }
    </style>
</head>
<body>
    <nav class="top-nav">
        <div class="nav-content">
            <div class="logo">
                <div class="logo-text">
                    <h1>Agent Q&A Manager</h1>
                    <p>Real-time Question Management</p>
                </div>
            </div>
            <div class="nav-stats">
                <div class="nav-stat">
                    <span class="nav-stat-value" id="stat-total">0</span>
                    <span class="nav-stat-label">Total</span>
                </div>
                <div class="nav-stat">
                    <span class="nav-stat-value" id="stat-answered">0</span>
                    <span class="nav-stat-label">Answered</span>
                </div>
                <div class="nav-stat">
                    <span class="nav-stat-value" id="stat-unanswered">0</span>
                    <span class="nav-stat-label">Pending</span>
                </div>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="main-layout">
            <div class="section">
                <div class="section-header">
                    <h2 class="section-title">
                        <span>Pending Questions</span>
                    </h2>
                    <span class="section-badge" id="pending-count">0</span>
                </div>
                <div class="section-body" id="unanswered-list">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Loading questions...</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-header">
                    <h2 class="section-title">
                        <span>Answered</span>
                    </h2>
                    <span class="section-badge" id="answered-count">0</span>
                </div>
                <div class="section-body" id="answered-list">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Loading answers...</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <button class="refresh-btn" onclick="loadAllData()" title="Refresh Data"></button>

    <script>
        const API_BASE = '';

        async function loadAllData() {
            await Promise.all([
                loadStats(),
                loadUnanswered(),
                loadAnswered()
            ]);
        }

        async function loadStats() {
            try {
                const response = await fetch(`${API_BASE}/api/stats`);
                const stats = await response.json();
                
                document.getElementById('stat-total').textContent = stats.total;
                document.getElementById('stat-answered').textContent = stats.answered;
                document.getElementById('stat-unanswered').textContent = stats.unanswered;
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        async function loadUnanswered() {
            try {
                const response = await fetch(`${API_BASE}/api/unanswered`);
                const questions = await response.json();
                
                const container = document.getElementById('unanswered-list');
                document.getElementById('pending-count').textContent = questions.length;
                
                if (questions.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <p class="empty-state-text">No pending questions!</p>
                        </div>
                    `;
                    return;
                }
                
                const savedValues = {};
                questions.forEach(q => {
                    const textareaId = `answer-${btoa(q.question)}`;
                    const textarea = document.getElementById(textareaId);
                    if (textarea) {
                        savedValues[textareaId] = textarea.value;
                    }
                });
                
                container.innerHTML = questions.map(q => `
                    <div class="question-card">
                        <div class="question-header">
                            <div class="question-text">${escapeHtml(q.question)}</div>
                        </div>
                        <div class="question-meta">
                            <div class="meta-item">
                                <span class="meta-icon"></span>
                                <span>${q.timestamp}</span>
                            </div>
                            <div class="meta-item">
                                <span class="meta-icon"></span>
                                <span>${q.caller_phone}</span>
                            </div>
                        </div>
                        <textarea id="answer-${btoa(q.question)}" placeholder="Type your answer here..."></textarea>
                        <div class="btn-group">
                            <button class="btn btn-primary" onclick="submitAnswer('${escapeHtml(q.question)}', 'answer-${btoa(q.question)}')">
                                Submit Answer
                            </button>
                            <button class="btn btn-danger" onclick="deleteQuestion('${escapeHtml(q.question)}')">
                            </button>
                        </div>
                    </div>
                `).join('');
                
                Object.keys(savedValues).forEach(textareaId => {
                    const textarea = document.getElementById(textareaId);
                    if (textarea && savedValues[textareaId]) {
                        textarea.value = savedValues[textareaId];
                    }
                });
            } catch (error) {
                console.error('Error loading unanswered questions:', error);
                document.getElementById('unanswered-list').innerHTML = `
                    <div class="empty-state">
                        <p style="color: #dc3545;">Error loading questions</p>
                    </div>
                `;
            }
        }

        async function loadAnswered() {
            try {
                const response = await fetch(`${API_BASE}/api/answered`);
                const questions = await response.json();
                
                const container = document.getElementById('answered-list');
                document.getElementById('answered-count').textContent = questions.length;
                
                if (questions.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <p class="empty-state-text">No answered questions yet</p>
                        </div>
                    `;
                    return;
                }
                
                container.innerHTML = questions.map(q => `
                    <div class="answered-item">
                        <div class="answered-question">
                            <span class="answer-icon"></span>
                            <span>${escapeHtml(q.question)}</span>
                        </div>
                        <div class="answered-answer">${escapeHtml(q.answer)}</div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading answered questions:', error);
                document.getElementById('answered-list').innerHTML = `
                    <div class="empty-state">
                        <p style="color: #dc3545;">Error loading answers</p>
                    </div>
                `;
            }
        }

        async function submitAnswer(question, textareaId) {
            const textarea = document.getElementById(textareaId);
            const answer = textarea.value.trim();
            
            if (!answer) {
                showNotification('Please enter an answer', 'error');
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/api/answer`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ question, answer })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showNotification('Answer submitted successfully!', 'success');
                    await loadAllData();
                } else {
                    showNotification(result.error || 'Failed to submit answer', 'error');
                }
            } catch (error) {
                console.error('Error submitting answer:', error);
                showNotification('Error submitting answer', 'error');
            }
        }

        async function deleteQuestion(question) {
            if (!confirm('Are you sure you want to delete this question?')) {
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/api/delete`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ question })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showNotification('Question deleted successfully!', 'success');
                    await loadAllData();
                } else {
                    showNotification(result.error || 'Failed to delete question', 'error');
                }
            } catch (error) {
                console.error('Error deleting question:', error);
                showNotification('Error deleting question', 'error');
            }
        }

        function showNotification(message, type) {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            
            const icon = type === 'success' ? '' : '';
            notification.innerHTML = `<span>${icon}</span><span>${message}</span>`;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 3000);
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        setInterval(loadAllData, 5000);

        loadAllData();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    stats = get_knowledge_stats()
    return stats

@app.get("/api/unanswered", response_model=List[QuestionItem])
async def get_unanswered():
    questions = get_unanswered_questions()
    return questions

@app.get("/api/answered", response_model=List[AnsweredItem])
async def get_answered():
    questions = get_answered_questions()
    result = [{'question': q, 'answer': a} for q, a in questions.items()]
    return result

@app.post("/api/answer")
async def answer_question(request: AnswerRequest):
    try:
        question = request.question.strip()
        answer = request.answer.strip()
        
        if not question or not answer:
            raise HTTPException(status_code=400, detail="Question and answer are required")
        
        # Read all rows
        rows = []
        found = False
        
        if not os.path.exists(KNOWLEDGE_FILE):
            initialize_knowledge_base()
        
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row['question'].lower().strip() == question.lower().strip():
                    row['answer'] = answer
                    row['answered'] = 'yes'
                    found = True
                rows.append(row)
        
        if not found:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Write back
        with open(KNOWLEDGE_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        return {'success': True, 'message': 'Answer saved successfully'}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/delete")
async def delete_question(request: DeleteRequest):
    try:
        question = request.question.strip()
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Read all rows except the one to delete
        rows = []
        found = False
        
        if not os.path.exists(KNOWLEDGE_FILE):
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row['question'].lower().strip() == question.lower().strip():
                    found = True
                    continue  # Skip this row (delete it)
                rows.append(row)
        
        if not found:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Write back
        with open(KNOWLEDGE_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        return {'success': True, 'message': 'Question deleted successfully'}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    initialize_knowledge_base()
    print("Starting Telephony Agent Q&A Manager...")
    print("📱 Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)
