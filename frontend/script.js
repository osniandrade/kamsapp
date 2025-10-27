const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const sendBtn = document.getElementById("sendBtn");

let selectedFiles = [];

dropzone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (e) => {
  selectedFiles = Array.from(e.target.files);
  updateDropzoneText();
});

dropzone.addEventListener("dragover", (e) => e.preventDefault());
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  selectedFiles = Array.from(e.dataTransfer.files);
  updateDropzoneText();
});

function updateDropzoneText() {
  if (selectedFiles.length === 0) {
    dropzone.textContent = "Arraste seus arquivos de áudio aqui (múltiplos arquivos aceitos)";
  } else {
    dropzone.textContent = `${selectedFiles.length} arquivo(s) selecionado(s): ${selectedFiles.map(f => f.name).join(", ")}`;
  }
}

sendBtn.addEventListener("click", async () => {
  if (selectedFiles.length === 0) return alert("Selecione ao menos um arquivo de áudio.");
  const template = document.getElementById("template").value;
  const resultsDiv = document.getElementById("results");
  
  resultsDiv.innerHTML = "<p>Processando arquivos...</p>";
  
  const allTranscripts = [];
  
  // Processa cada arquivo e coleta transcrições
  for (let i = 0; i < selectedFiles.length; i++) {
    const file = selectedFiles[i];
    const formData = new FormData();
    formData.append("audio", file);
    formData.append("report_template", template);

    const fileResultDiv = document.createElement("div");
    fileResultDiv.style.marginBottom = "30px";
    fileResultDiv.style.borderBottom = "2px solid #ccc";
    fileResultDiv.style.paddingBottom = "20px";
    fileResultDiv.innerHTML = `<h4>📁 ${file.name}</h4><p>Transcrevendo...</p>`;
    resultsDiv.appendChild(fileResultDiv);

    try {
      const res = await fetch("http://192.168.0.30:8000/process_audio", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      
      if (data.error) {
        fileResultDiv.innerHTML = `
          <h4>📁 ${file.name}</h4>
          <p style="color: red;">❌ Erro: ${data.error}</p>
        `;
      } else {
        fileResultDiv.innerHTML = `
          <h4>📁 ${file.name}</h4>
          <h5>✅ Transcrição:</h5>
          <pre>${data.transcript || "Sem transcrição"}</pre>
        `;
        
        // Adiciona à lista de transcrições
        allTranscripts.push({
          filename: data.filename,
          transcript: data.transcript
        });
      }
    } catch (error) {
      fileResultDiv.innerHTML = `
        <h4>📁 ${file.name}</h4>
        <p style="color: red;">❌ Erro na requisição: ${error.message}</p>
      `;
    }
  }
  
  // Clear first "Processing" message
  if (resultsDiv.firstChild && resultsDiv.firstChild.tagName === "P") {
    resultsDiv.removeChild(resultsDiv.firstChild);
  }
  
  // Se temos transcrições, gera o relatório consolidado
  if (allTranscripts.length > 0) {
    const reportDiv = document.createElement("div");
    reportDiv.style.marginTop = "40px";
    reportDiv.style.padding = "20px";
    reportDiv.style.backgroundColor = "#f0f8ff";
    reportDiv.style.border = "3px solid #4CAF50";
    reportDiv.style.borderRadius = "10px";
    reportDiv.innerHTML = `<h3>📝 Gerando relatório consolidado com ${allTranscripts.length} arquivo(s)...</h3>`;
    resultsDiv.appendChild(reportDiv);
    
    try {
      const formData = new FormData();
      formData.append("transcripts", JSON.stringify(allTranscripts));
      formData.append("report_template", template);
      
      const res = await fetch("http://192.168.0.30:8000/generate_report", {
        method: "POST",
        body: formData,
      });
      
      const data = await res.json();
      
      if (data.error) {
        reportDiv.innerHTML = `
          <h3>❌ Erro ao gerar relatório</h3>
          <p style="color: red;">${data.error}</p>
        `;
      } else {
        reportDiv.innerHTML = `
          <h3>✅ Relatório Consolidado</h3>
          <div style="background: white; padding: 15px; border-radius: 5px;">
            <pre style="white-space: pre-wrap;">${data.report}</pre>
          </div>
        `;
      }
    } catch (error) {
      reportDiv.innerHTML = `
        <h3>❌ Erro ao gerar relatório</h3>
        <p style="color: red;">${error.message}</p>
      `;
    }
  }
});
