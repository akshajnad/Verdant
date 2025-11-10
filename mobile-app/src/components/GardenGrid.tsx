/**
 * Garden Grid Component - Interactive map editor
 */
import React from 'react';
import { View, Text, Pressable, ScrollView } from 'react-native';

export interface Cell {
  r: number;
  c: number;
  label?: string;
  plant_catalog_id?: string;
}

interface GardenGridProps {
  rows: number;
  cols: number;
  cells: Cell[];
  onPressCell?: (row: number, col: number) => void;
  editable?: boolean;
}

export default function GardenGrid({
  rows,
  cols,
  cells,
  onPressCell,
  editable = false,
}: GardenGridProps) {
  function getCell(r: number, c: number): Cell | undefined {
    return cells.find((cell) => cell.r === r && cell.c === c);
  }

  function getCellColor(cell?: Cell): string {
    if (!cell?.label) return 'bg-gray-100';

    // Color code by plant type (simplified)
    const label = cell.label.toLowerCase();
    if (label.includes('tomato') || label.includes('pepper')) return 'bg-red-200';
    if (label.includes('lettuce') || label.includes('kale')) return 'bg-green-200';
    if (label.includes('carrot') || label.includes('potato')) return 'bg-orange-200';
    if (label.includes('corn')) return 'bg-yellow-200';

    return 'bg-verdant-200';
  }

  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false}>
      <View className="border-2 border-gray-300 rounded-2xl overflow-hidden bg-white">
        {Array.from({ length: rows }).map((_, r) => (
          <View key={r} className="flex-row">
            {Array.from({ length: cols }).map((_, c) => {
              const cell = getCell(r, c);
              const bgColor = getCellColor(cell);

              return (
                <Pressable
                  key={`${r}-${c}`}
                  className={`w-16 h-16 border border-gray-200 items-center justify-center ${bgColor}`}
                  onPress={() => editable && onPressCell?.(r, c)}
                  disabled={!editable}
                >
                  {cell?.label ? (
                    <Text className="text-xs font-medium text-center px-1" numberOfLines={2}>
                      {cell.label}
                    </Text>
                  ) : (
                    <Text className="text-gray-400 text-xs">
                      {r},{c}
                    </Text>
                  )}
                </Pressable>
              );
            })}
          </View>
        ))}
      </View>
    </ScrollView>
  );
}
