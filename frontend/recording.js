let canvas, ctx;
let currentInterviewId = null;
let currentUserId = null;
let currentQuestionId = null;
let currentInterviewName = null;
let currentQuestions = [];
let currentQuestionIndex = 0;
let currentSectionIndex = 0;
const sections = ["strengths", "weaknesses", "future", "challenges"];

// Add QuestionStatus enum at the top of the file
const QuestionStatus = {
    NOT_ATTEMPTED: 'NOT_ATTEMPTED',
    SKIPPED: 'SKIPPED',
    ANSWERED: 'ANSWERED'
};

// Media related variables
let mediaStreams = {
    screen: null,
    camera: null,
    audio: null
};
let mediaRecorders = {
    screen: null,
    camera: null,
    audio: null,
    combined: null
};
let screenChunks = [], cameraChunks = [], audioChunks = [], combinedChunks = [];
let isInterviewActive = false;

// Add audio management at the top with other variables
let currentAudioElement = null;

// Add at the top with other variables
let videoElement = null;
let animationFrameId = null;

// Add authentication helper functions
function isAuthenticated() {
    return !!localStorage.getItem('token');
}

async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }

    // Don't add Content-Type for FormData
    const headers = options.body instanceof FormData
        ? { 'Authorization': `Bearer ${token}` }
        : {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          };

    const authOptions = {
        ...options,
        headers: {
            ...headers,
            ...options.headers
        }
    };

    return fetch(url, authOptions);
}

// Get interview ID from URL parameters
const urlParams = new URLSearchParams(window.location.search);
const interviewId = urlParams.get('id');

async function fetchSectionQuestions(section) {
    try {
        const response = await fetchWithAuth(
            `${API_CONFIG.API_URL}/get_section_questions?section=${section}&interview_id=${currentInterviewId}`
        );
        const data = await response.json();
        currentQuestions = data.questions;
        return currentQuestions;
    } catch (error) {
        console.error('Error fetching section questions:', error);
        return null;
    }
}

// Update the updateQuestionStatus function
async function updateQuestionStatus(questionId, status, recordingPath = null) {
    try {
        console.log('Updating question status:', { questionId, status, recordingPath });
        
        const response = await fetchWithAuth(`${API_CONFIG.API_URL}/update_question_status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question_id: questionId,
                status: QuestionStatus[status], // Use enum value
                recording_path: recordingPath
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Failed to update status: ${JSON.stringify(errorData)}`);
        }

        const data = await response.json();
        console.log('Status update response:', data);
        return data;
    } catch (error) {
        console.error('Error updating question status:', error);
        throw error;
    }
}

// Update displayQuestion function with better audio management
async function displayQuestion(index) {
    if (!currentQuestions || !currentQuestions[index]) {
        console.error('Invalid question index or no questions loaded');
        return;
    }

    try {
        const question = currentQuestions[index];
        document.getElementById('question').textContent = question.text;
        currentQuestionId = question.id;

        // Cleanup previous audio
        if (currentAudioElement) {
            currentAudioElement.pause();
            URL.revokeObjectURL(currentAudioElement.src);
            currentAudioElement = null;
        }

        // Play question audio
        console.log('Fetching audio for question:', question.text);
        const audioResponse = await fetchWithAuth(
            `${API_CONFIG.API_URL}/get_question_audio?text=${encodeURIComponent(question.text)}`
        );
        
        if (!audioResponse.ok) {
            throw new Error('Failed to fetch question audio');
        }

        const audioBlob = await audioResponse.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Use existing audio element from DOM
        const audioElement = document.getElementById('questionAudio');
        audioElement.src = audioUrl;
        currentAudioElement = audioElement;
        
        await audioElement.play().catch(err => {
            console.error('Error playing audio:', err);
        });
        
        console.log('Question audio playing');
        updateSectionInfo();
    } catch (error) {
        console.error('Error displaying question:', error);
        throw error;
    }
}

// Add replay button handler
document.getElementById('replayBtn')?.addEventListener('click', () => {
    const audioElement = document.getElementById('questionAudio');
    audioElement.currentTime = 0;
    audioElement.play();
});

function initializeBottomNav(totalQuestions) {
    const bottomNav = document.getElementById('bottomNav');
    bottomNav.innerHTML = '';

    for (let i = 0; i < totalQuestions; i++) {
        const navItem = document.createElement('div');
        navItem.className = `w-3 h-3 rounded-full cursor-pointer transition-all duration-200 ${
            i === currentQuestionIndex ? 'bg-blue-500' : 'bg-gray-300 hover:bg-gray-400'
        }`;
        navItem.addEventListener('click', () => {
            currentQuestionIndex = i;
            displayQuestion(i);
        });
        bottomNav.appendChild(navItem);
    }
}

function updateBottomNav(index) {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach((item, i) => {
        item.classList.remove('bg-blue-500', 'text-white');
        item.classList.add('bg-gray-300', 'text-gray-700');
        if (i === index) {
            item.classList.add('bg-blue-500', 'text-white');
            item.classList.remove('bg-gray-300', 'text-gray-700');
        }
    });
}

// Update next button handler
document.getElementById('nextBtn')?.addEventListener('click', async () => {
    try {
        // Stop and upload current recording
        await stopRecordingAndUpload();

        // Mark current question as skipped if no recording
        if (currentQuestions[currentQuestionIndex] && !currentQuestions[currentQuestionIndex].recording_path) {
            await updateQuestionStatus(currentQuestions[currentQuestionIndex].id, QuestionStatus.SKIPPED);
        }

        // Move to next question or section
        if (currentQuestionIndex < currentQuestions.length - 1) {
            currentQuestionIndex++;
            await displayQuestion(currentQuestionIndex);
            startRecording();
        } else if (currentSectionIndex < sections.length - 1) {
            currentSectionIndex++;
            console.log(`Moving to section: ${sections[currentSectionIndex]}`);
            const newQuestions = await loadSectionQuestions(sections[currentSectionIndex]);
            
            if (newQuestions) {
                currentQuestionIndex = 0;
                await displayQuestion(0);
                startRecording();
            } else {
                throw new Error('Failed to load next section questions');
            }
        } else {
            alert('Interview completed! Thank you for your participation.');
            window.location.href = '/index.html';
        }
    } catch (error) {
        console.error('Error handling next question:', error);
        alert('There was an error moving to the next question. Please try again.');
    }
});

document.addEventListener('DOMContentLoaded', async () => {
    if (!isAuthenticated()) {
        window.location.href = '/login.html';
        return;
    }

    try {
        // Get user info
        const userResponse = await fetchWithAuth(`${API_CONFIG.API_URL}/user/me`);
        const userData = await userResponse.json();
        currentUserId = userData.email;

        // Get interview ID from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        currentInterviewId = urlParams.get('id');

        if (!currentInterviewId) {
            throw new Error('No interview ID provided');
        }

        // Initialize first section
        await loadSectionQuestions(sections[currentSectionIndex]);
    } catch (error) {
        console.error('Error initializing recording page:', error);
        alert('Failed to initialize recording. Redirecting to home page.');
        window.location.href = '/index.html';
    }
});

async function loadSectionQuestions(section) {
    try {
        console.log(`Loading questions for section: ${section}`);
        const response = await fetchWithAuth(
            `${API_CONFIG.API_URL}/get_section_questions?section=${section}&interview_id=${currentInterviewId}`
        );
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to fetch questions');
        }
        
        console.log('Received questions:', data);
        
        if (!data.questions || data.questions.length === 0) {
            throw new Error(`No questions received for section: ${section}`);
        }
        
        currentQuestions = data.questions;
        currentSection = section;
        updateSectionInfo();
        return currentQuestions;
    } catch (error) {
        console.error('Error loading section questions:', error);
        alert(`Failed to load questions for ${section} section. Please try again.`);
        return null;
    }
}

// Update the updateSectionInfo function
function updateSectionInfo() {
    const sectionInfo = document.getElementById('sectionInfo');
    if (sectionInfo) {
        const sectionName = currentSection.charAt(0).toUpperCase() + currentSection.slice(1);
        const progress = Math.round((currentQuestionIndex + 1) / currentQuestions.length * 100);
        
        sectionInfo.innerHTML = `
            <div class="mb-2 text-white">Section: ${sectionName}</div>
            <div class="w-full bg-gray-700 rounded-full h-2">
                <div class="bg-blue-500 rounded-full h-2" style="width: ${progress}%"></div>
            </div>
            <div class="text-xs mt-1 text-gray-300">
                Question ${currentQuestionIndex + 1} of ${currentQuestions.length}
            </div>
        `;
    }
}

// ... copy existing recording functionality from app.js ...

// Update the sendFile function to use the enum
async function sendFile(blob, type) {
    if (blob.size === 0) {
        console.error(`${type} blob is empty, not sending to server.`);
        return;
    }

    try {
        // Create form data
        const formData = new FormData();
        const fileName = `${currentUserId}-${currentInterviewId}-${currentQuestionId}_${type}.webm`;
        
        // Add all required fields to form data
        formData.append('file', new File([blob], fileName, { type: 'video/webm' }));
        formData.append('interview_id', currentInterviewId);
        formData.append('question_id', currentQuestionId);
        formData.append('file_type', type);

        console.log('Sending file upload request:', {
            fileName,
            interviewId: currentInterviewId,
            questionId: currentQuestionId,
            fileType: type
        });

        const response = await fetchWithAuth(`${API_CONFIG.API_URL}/upload`, {
            method: 'POST',
            // Don't set Content-Type header - let browser set it with boundary
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Upload failed: ${JSON.stringify(errorData.detail || errorData)}`);
        }

        const data = await response.json();
        console.log(`${type} file uploaded successfully:`, data);

        if (type === 'combined' && currentQuestionId) {
            await updateQuestionStatus(
                currentQuestionId,
                QuestionStatus.ANSWERED,
                data.path
            );
        }

        return data;
    } catch (error) {
        console.error(`Error uploading ${type} file:`, error);
        throw error;
    }
}

// Add event listeners after DOM content is loaded
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('startBtn')?.addEventListener('click', async () => {
        try {
            await startRecording();
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            document.getElementById('nextBtn').disabled = false;
        } catch (error) {
            console.error('Error starting interview:', error);
            alert('Failed to start interview. Please try again.');
        }
    });

    document.getElementById('stopBtn')?.addEventListener('click', async () => {
        try {
            await stopRecordingAndUpload();
            cleanupResources();
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('nextBtn').disabled = true;
        } catch (error) {
            console.error('Error ending interview:', error);
        }
    });
});

// Update camera display setup
async function setupCameraDisplay() {
    try {
        if (!mediaStreams.camera) {
            console.error('Camera stream not initialized');
            return;
        }

        // Create and setup video element for display
        if (!videoElement) {
            videoElement = document.createElement('video');
            videoElement.autoplay = true;
            videoElement.playsInline = true;
            videoElement.muted = true;
        }

        // Set up canvas
        canvas = document.getElementById('canvas');
        if (!canvas) {
            console.error('Canvas element not found');
            return;
        }
        
        ctx = canvas.getContext('2d');
        canvas.width = 280;
        canvas.height = 210;

        // Connect camera stream to video element
        videoElement.srcObject = mediaStreams.camera;
        await videoElement.play();

        // Start drawing loop
        function drawFrame() {
            if (mediaStreams.camera.active) {
                const { videoWidth, videoHeight } = videoElement;
                const scale = Math.min(
                    canvas.width / videoWidth,
                    canvas.height / videoHeight
                );
                
                const drawWidth = videoWidth * scale;
                const drawHeight = videoHeight * scale;
                const x = (canvas.width - drawWidth) / 2;
                const y = (canvas.height - drawHeight) / 2;

                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(videoElement, x, y, drawWidth, drawHeight);
            }
            animationFrameId = requestAnimationFrame(drawFrame);
        }

        drawFrame();
        console.log('Camera display initialized successfully');

    } catch (error) {
        console.error('Error setting up camera display:', error);
    }
}

// Update initializeInterview function
async function initializeInterview() {
    try {
        console.log('Initializing interview...');
        
        // Get camera stream first
        if (!mediaStreams.camera) {
            mediaStreams.camera = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: 1280, 
                    height: 720,
                    facingMode: 'user'
                },
                audio: false 
            });
            
            // Setup camera display immediately after getting stream
            await setupCameraDisplay();
        }

        // Get other streams
        if (!mediaStreams.screen) {
            mediaStreams.screen = await navigator.mediaDevices.getDisplayMedia({ video: true });
        }
        if (!mediaStreams.audio) {
            mediaStreams.audio = await navigator.mediaDevices.getUserMedia({ audio: true });
        }

        isInterviewActive = true;
        return true;
    } catch (error) {
        console.error('Failed to initialize interview:', error);
        return false;
    }
}

async function startRecording() {
    if (!isInterviewActive) {
        const initialized = await initializeInterview();
        if (!initialized) {
            throw new Error('Failed to initialize interview');
        }
    }

    try {
        // Create new recorders
        mediaRecorders.screen = new MediaRecorder(mediaStreams.screen);
        mediaRecorders.camera = new MediaRecorder(mediaStreams.camera);
        mediaRecorders.audio = new MediaRecorder(mediaStreams.audio);

        const combinedStream = new MediaStream([
            ...mediaStreams.screen.getTracks(),
            ...mediaStreams.camera.getTracks(),
            ...mediaStreams.audio.getTracks()
        ]);
        mediaRecorders.combined = new MediaRecorder(combinedStream);

        // Reset chunks
        screenChunks = [];
        cameraChunks = [];
        audioChunks = [];
        combinedChunks = [];

        // Set up handlers
        mediaRecorders.screen.ondataavailable = e => screenChunks.push(e.data);
        mediaRecorders.camera.ondataavailable = e => cameraChunks.push(e.data);
        mediaRecorders.audio.ondataavailable = e => audioChunks.push(e.data);
        mediaRecorders.combined.ondataavailable = e => combinedChunks.push(e.data);

        // Start recording
        Object.values(mediaRecorders).forEach(recorder => recorder.start());
        console.log('Recording started');
    } catch (error) {
        console.error('Failed to start recording:', error);
        throw error;
    }
}

// Update stopRecordingAndUpload
async function stopRecordingAndUpload() {
    try {
        // Only stop recorders, keep streams active for next recording
        Object.values(mediaRecorders).forEach(recorder => {
            if (recorder && recorder.state === 'recording') {
                recorder.stop();
            }
        });

        await uploadRecordings();

        // Clear recorder references but keep streams
        mediaRecorders = { screen: null, camera: null, audio: null, combined: null };
    } catch (error) {
        console.error('Error in stopRecordingAndUpload:', error);
        throw error;
    }
}

function cleanupMediaStreams() {
    Object.values(mediaStreams).forEach(stream => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });
    mediaStreams = { screen: null, camera: null, audio: null };
    mediaRecorders = { screen: null, camera: null, audio: null, combined: null };
    isInterviewActive = false;
}

// Add uploadRecordings function after existing media handling functions
async function uploadRecordings() {
    try {
        console.log('Starting upload process...');
        
        // Wait for data to be available
        await Promise.all([
            new Promise(resolve => mediaRecorders.screen.addEventListener('dataavailable', resolve, { once: true })),
            new Promise(resolve => mediaRecorders.camera.addEventListener('dataavailable', resolve, { once: true })),
            new Promise(resolve => mediaRecorders.audio.addEventListener('dataavailable', resolve, { once: true })),
            new Promise(resolve => mediaRecorders.combined.addEventListener('dataavailable', resolve, { once: true }))
        ]);

        // Create files from chunks
        const files = {
            screen: new File([new Blob(screenChunks)], `${currentUserId}-${currentInterviewId}-${currentQuestionId}_screen.webm`),
            camera: new File([new Blob(cameraChunks)], `${currentUserId}-${currentInterviewId}-${currentQuestionId}_camera.webm`),
            audio: new File([new Blob(audioChunks)], `${currentUserId}-${currentInterviewId}-${currentQuestionId}_audio.webm`),
            combined: new File([new Blob(combinedChunks)], `${currentUserId}-${currentInterviewId}-${currentQuestionId}_combined.webm`)
        };

        // Upload each file
        for (const [type, file] of Object.entries(files)) {
            if (file.size === 0) {
                console.warn(`${type} recording is empty, skipping upload`);
                continue;
            }

            const formData = new FormData();
            formData.append('file', file);
            formData.append('interview_id', currentInterviewId);
            formData.append('question_id', currentQuestionId);
            formData.append('file_type', type);

            console.log(`Uploading ${type} file:`, file.name);
            const response = await fetchWithAuth(`${API_CONFIG.API_URL}/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Failed to upload ${type} file: ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`${type} file uploaded successfully:`, data);
        }

        return true;
    } catch (error) {
        console.error('Error uploading recordings:', error);
        throw error;
    }
}

// Add cleanup on interview end
// Update cleanup function
function cleanupResources() {
    // Stop the animation frame
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }

    // Clean up video element
    if (videoElement) {
        videoElement.pause();
        videoElement.srcObject = null;
        videoElement = null;
    }

    // Clean up canvas
    if (ctx && canvas) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }

    // Clean up media resources
    Object.values(mediaRecorders).forEach(recorder => {
        if (recorder && recorder.state === 'recording') {
            recorder.stop();
        }
    });

    Object.values(mediaStreams).forEach(stream => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });

    mediaStreams = { screen: null, camera: null, audio: null };
    mediaRecorders = { screen: null, camera: null, audio: null, combined: null };
    isInterviewActive = false;
}

// Add cleanup on page unload
window.addEventListener('beforeunload', () => {
    cleanupResources();
});