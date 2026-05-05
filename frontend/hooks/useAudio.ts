import { Audio } from "expo-av";

export async function startRecording() {
  await Audio.requestPermissionsAsync();

  const recording = new Audio.Recording();

  await recording.prepareToRecordAsync(
    Audio.RecordingOptionsPresets.HIGH_QUALITY
  );

  await recording.startAsync();

  return recording;
}