const BASE_URL = "http://127.0.0.1:8000";

export async function uploadAudio(file: any) {
  const formData = new FormData();

  formData.append("file", {
    uri: file.uri,
    name: "audio.wav",
    type: "audio/wav",
  } as any);

  const res = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return res.json();
}