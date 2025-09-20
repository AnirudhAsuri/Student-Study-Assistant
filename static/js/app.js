// Student Study Assistant Frontend JavaScript

class StudyAssistant {
    constructor() {
        this.files = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateStatus();
        this.loadFiles();
        
        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    setupEventListeners() {
        // File upload
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');

        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
        dropZone.addEventListener('drop', this.handleDrop.bind(this));
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));

        // Q&A
        const askButton = document.getElementById('ask-button');
        const questionInput = document.getElementById('question-input');
        
        askButton.addEventListener('click', this.askQuestion.bind(this));
        questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.askQuestion();
        });

        // Study material generation
        const generateButton = document.getElementById('generate-button');
        generateButton.addEventListener('click', this.generateMaterial.bind(this));

        // Copy material
        const copyButton = document.getElementById('copy-material');
        copyButton.addEventListener('click', this.copyMaterial.bind(this));

        // Status refresh
        const refreshButton = document.getElementById('refresh-status');
        refreshButton.addEventListener('click', this.updateStatus.bind(this));
    }

    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('drop-zone').classList.add('border-blue-500');
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('drop-zone').classList.remove('border-blue-500');
        
        const files = Array.from(e.dataTransfer.files);
        this.uploadFiles(files);
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.uploadFiles(files);
    }

    async uploadFiles(files) {
        const progressContainer = document.getElementById('upload-progress');
        const progressBar = document.getElementById('progress-bar');
        const uploadStatus = document.getElementById('upload-status');

        progressContainer.classList.remove('hidden');
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const progress = ((i + 1) / files.length) * 100;
            
            progressBar.style.width = `${progress}%`;
            uploadStatus.textContent = `Uploading ${file.name}...`;

            try {
                await this.uploadSingleFile(file);
            } catch (error) {
                this.showNotification(`Error uploading ${file.name}: ${error.message}`, 'error');
            }
        }

        progressContainer.classList.add('hidden');
        this.loadFiles();
        this.updateStatus();
    }

    async uploadSingleFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();
        this.showNotification(`Successfully uploaded ${file.name}`, 'success');
        return result;
    }

    async loadFiles() {
        try {
            const response = await fetch('/files');
            const data = await response.json();
            this.files = data.files;
            this.renderFileList();
            this.updateUIState();
        } catch (error) {
            console.error('Error loading files:', error);
        }
    }

    renderFileList() {
        const fileList = document.getElementById('file-list');
        
        if (this.files.length === 0) {
            fileList.innerHTML = '<p class="text-gray-500 text-sm italic">No files uploaded yet</p>';
            return;
        }

        fileList.innerHTML = this.files.map(file => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                <div class="flex items-center space-x-3">
                    <i data-lucide="${file.filename.endsWith('.pdf') ? 'file-text' : 'file'}" class="w-4 h-4 text-gray-500"></i>
                    <div>
                        <p class="font-medium text-sm text-gray-800">${file.filename}</p>
                        <p class="text-xs text-gray-500">${this.formatFileSize(file.size)} • ${file.status}</p>
                    </div>
                </div>
                <button onclick="app.deleteFile('${file.id}')" class="text-red-500 hover:text-red-700 transition-colors">
                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                </button>
            </div>
        `).join('');
        
        // Reinitialize icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    async deleteFile(fileId) {
        if (!confirm('Are you sure you want to delete this file?')) return;

        try {
            const response = await fetch(`/files/${fileId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showNotification('File deleted successfully', 'success');
                this.loadFiles();
                this.updateStatus();
            } else {
                throw new Error('Delete failed');
            }
        } catch (error) {
            this.showNotification('Error deleting file', 'error');
        }
    }

    async askQuestion() {
        const questionInput = document.getElementById('question-input');
        const question = questionInput.value.trim();

        if (!question) {
            this.showNotification('Please enter a question', 'warning');
            return;
        }

        this.showLoading('Searching for relevant information...');

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'Failed to get answer');
            }

            this.displayAnswer(question, result);
            questionInput.value = '';
        } catch (error) {
            this.showNotification(`Error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayAnswer(question, result) {
        const answerSection = document.getElementById('answer-section');
        const answerContent = document.getElementById('answer-content');
        const sourcesList = document.getElementById('sources-list');

        answerContent.innerHTML = `
            <div class="mb-3">
                <strong>Question:</strong> ${question}
            </div>
            <div>${result.answer.replace(/\n/g, '<br>')}</div>
        `;

        if (result.sources && result.sources.length > 0) {
            sourcesList.innerHTML = result.sources.map(source => `
                <div class="text-xs text-blue-600">
                    📄 ${source.filename} (similarity: ${(source.similarity * 100).toFixed(1)}%)
                </div>
            `).join('');
        } else {
            sourcesList.innerHTML = '<div class="text-xs text-blue-600">No specific sources found</div>';
        }

        answerSection.classList.remove('hidden');
        answerSection.scrollIntoView({ behavior: 'smooth' });
    }

    async generateMaterial() {
        const materialType = document.getElementById('material-type').value;
        const topic = document.getElementById('topic-input').value.trim();

        this.showLoading(`Generating ${materialType}...`);

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    material_type: materialType,
                    topic: topic || null
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'Failed to generate material');
            }

            this.displayMaterial(result);
        } catch (error) {
            this.showNotification(`Error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayMaterial(result) {
        const materialSection = document.getElementById('material-section');
        const materialTitle = document.getElementById('material-title');
        const materialContent = document.getElementById('material-content');

        materialTitle.textContent = `Generated ${result.material_type.charAt(0).toUpperCase() + result.material_type.slice(1)}`;
        materialContent.textContent = result.content;

        materialSection.classList.remove('hidden');
        materialSection.scrollIntoView({ behavior: 'smooth' });
    }

    async copyMaterial() {
        const materialContent = document.getElementById('material-content');
        try {
            await navigator.clipboard.writeText(materialContent.textContent);
            this.showNotification('Copied to clipboard!', 'success');
        } catch (error) {
            this.showNotification('Failed to copy to clipboard', 'error');
        }
    }

    async updateStatus() {
        try {
            const response = await fetch('/status');
            const status = await response.json();

            const statusIndicator = document.getElementById('status-indicator');
            const statusText = document.getElementById('status-text');
            const fileCount = document.getElementById('file-count');
            const chunkCount = document.getElementById('chunk-count');

            if (status.groq_available) {
                statusIndicator.className = 'w-3 h-3 bg-green-500 rounded-full mr-2';
                statusText.textContent = 'Ready';
            } else {
                statusIndicator.className = 'w-3 h-3 bg-red-500 rounded-full mr-2';
                statusText.textContent = 'Groq API Unavailable';
            }

            fileCount.textContent = status.uploaded_files;
            chunkCount.textContent = status.total_chunks;

        } catch (error) {
            console.error('Error updating status:', error);
        }
    }

    updateUIState() {
        const hasFiles = this.files.length > 0;
        
        // Enable/disable inputs based on whether files are uploaded
        document.getElementById('question-input').disabled = !hasFiles;
        document.getElementById('ask-button').disabled = !hasFiles;
        document.getElementById('material-type').disabled = !hasFiles;
        document.getElementById('topic-input').disabled = !hasFiles;
        document.getElementById('generate-button').disabled = !hasFiles;

        if (!hasFiles) {
            document.getElementById('question-input').placeholder = 'Upload documents first to ask questions...';
        } else {
            document.getElementById('question-input').placeholder = 'Ask a question about your study materials...';
        }
    }

    showLoading(text) {
        document.getElementById('loading-text').textContent = text;
        document.getElementById('loading-overlay').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }

    showNotification(message, type = 'info') {
        // Create a simple notification
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-4 py-2 rounded-lg text-white z-50 ${
            type === 'success' ? 'bg-green-500' :
            type === 'error' ? 'bg-red-500' :
            type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
        }`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize the application
const app = new StudyAssistant();