import { View, Text } from "react-native";

export default function TunerScreen() {
  return (
    <View className="flex-1 bg-black items-center justify-center">
      
      <Text className="text-zinc-400 text-lg">Standard Tuning</Text>

      <Text className="text-white text-7xl font-bold mt-6">
        A
      </Text>

      <Text className="text-zinc-500 text-lg mt-2">
        440 Hz
      </Text>

      <View className="w-64 h-2 bg-zinc-800 mt-10 rounded-full">
        <View className="w-1/2 h-full bg-white rounded-full" />
      </View>

    </View>
  );
}