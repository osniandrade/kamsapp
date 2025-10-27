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
  
  for (let i = 0; i < selectedFiles.length; i++) {
    const file = selectedFiles[i];
    const formData = new FormData();
    formData.append("audio", file);
    formData.append("report_template", template);

    const fileResultDiv = document.createElement("div");
    fileResultDiv.style.marginBottom = "30px";
    fileResultDiv.style.borderBottom = "2px solid #ccc";
    fileResultDiv.style.paddingBottom = "20px";
    fileResultDiv.innerHTML = `<h4>📁 ${file.name}</h4><p>Processando...</p>`;
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
          ${data.transcript ? `<h5>Transcrição parcial:</h5><pre>${data.transcript}</pre>` : ''}
        `;
      } else {
        fileResultDiv.innerHTML = `
          <h4>📁 ${file.name}</h4>
          <h5>✅ Transcrição:</h5>
          <pre>${data.transcript || "Sem transcrição"}</pre>
          <h5>📄 Relatório Gerado:</h5>
          <pre>${data.report || "Sem relatório"}</pre>
        `;
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
});
