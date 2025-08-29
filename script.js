// Set the worker source for PDF.js
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.11.338/pdf.worker.min.js`;

// Get references to our HTML elements
const pdfFileInput = document.getElementById('pdf-file-input');
const processPdfButton = document.getElementById('process-pdf-button');
const extractedTextOutput = document.getElementById('extracted-text-output');
const resultsOutput = document.getElementById('results-output');
const statusMessage = document.getElementById('status-message');

// --- PDF Processing Logic ---

processPdfButton.addEventListener('click', async () => {
    const file = pdfFileInput.files[0];
    if (!file) {
        statusMessage.textContent = 'No PDF file selected.';
        return;
    }
    // ... (rest of the validation) ...

    extractedTextOutput.textContent = "";
    resultsOutput.innerHTML = "";

    try {
        statusMessage.textContent = 'Extracting raw text from PDF...';
        const fileReader = new FileReader();

        fileReader.onload = async function() {
            // THE FIX IS ON THIS LINE: UintArray -> Uint8Array
            const typedarray = new Uint8Array(this.result);
            const pdf = await pdfjsLib.getDocument({ data: typedarray }).promise;
            let fullText = '';
            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const textContent = await page.getTextContent();
                const pageText = textContent.items.map(item => item.str).join(' ');
                fullText += pageText + '\n';
            }

            // SIMPLIFIED: Display the full raw text that will be sent
            const rawText = fullText.trim();
            extractedTextOutput.textContent = rawText;

            // Send the FULL raw text to the backend
            await getCptCodeEstimates(rawText);
        };

        fileReader.readAsArrayBuffer(file);

    } catch (error) {
        console.error('Error processing PDF:', error);
        statusMessage.textContent = `Error: Failed to process PDF. ${error.message}`;
    }
});


// --- Firebase Cloud Function Logic (No Changes Needed) ---

async function getCptCodeEstimates(text) {
    if (!text) {
        statusMessage.textContent = "Cannot send empty text.";
        return;
    }
    statusMessage.textContent = 'Sending note to AI for summarization and searching...';
    const findSimilarCptCodes = firebase.functions().httpsCallable('findSimilarCptCodes');
    try {
        const result = await findSimilarCptCodes({ text: text });
        const codes = result.data.results;
        displayResults(codes);
        statusMessage.textContent = 'Search complete!';
    } catch (error) {
        console.error("Error calling Cloud Function:", error);
        statusMessage.textContent = `Error: ${error.message}`;
        resultsOutput.innerHTML = `<p style="color: red;">An error occurred while searching.</p>`;
    }
}


// --- UI Display Logic (NO CHANGES NEEDED) ---
function displayResults(codes) {
    resultsOutput.innerHTML = "";
    if (!codes || codes.length === 0) {
        resultsOutput.innerHTML = '<p>No matching codes found.</p>';
        return;
    }
    let html = '<ul>';
    codes.forEach(code => {
        const codeNumber = code.cpt_code || 'N/A';
        const description = code.Descriptions || 'No description available.';
        html += `<li><strong>Code ${codeNumber}:</strong> ${description}</li>`;
    });
    html += '</ul>';
    resultsOutput.innerHTML = html;
}
