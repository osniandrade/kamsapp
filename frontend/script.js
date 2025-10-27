const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const sendBtn = document.getElementById("sendBtn");

let selectedFile = null;

dropzone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (e) => selectedFile = e.target.files[0]);

dropzone.addEventListener("dragover", (e) => e.preventDefault());
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  selectedFile = e.dataTransfer.files[0];
});

sendBtn.addEventListener("click", async () => {
  if (!selectedFile) return alert("Selecione um arquivo de áudio.");
  const template = document.getElementById("template").value;

  const formData = new FormData();
  formData.append("audio", selectedFile);
  formData.append("report_template", template);

  const res = await fetch("http://192.168.0.30:8000/process_audio", {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  document.getElementById("transcript").textContent = data.transcript || "Erro na transcrição";
  document.getElementById("report").textContent = data.report || "Erro ao gerar relatório";
});
