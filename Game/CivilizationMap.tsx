/**
 * CivilizationMap.tsx — Yksinkertainen kartta
 *
 * Yksinkertainen karttanäkymä provinsseista.
 */
import { useState } from 'react';
import { Province, FactionId, Army } from '@/types/province';

interface CivilizationMapProps {
  provinces: Province[];
  armies: Army[];
  selectedProvinceId: string | null;
  selectedArmyId: string | null;
  onProvinceClick: (provinceId: string) => void;
  onArmyClick: (armyId: string) => void;
  playerFaction: FactionId;
}

export const CivilizationMap = ({
  provinces,
  armies,
  selectedProvinceId,
  selectedArmyId,
  onProvinceClick,
  onArmyClick,
  playerFaction,
}: CivilizationMapProps) => {
  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Kartta</h2>
      <div className="grid grid-cols-4 gap-2">
        {provinces.map((province) => (
          <div
            key={province.id}
            className={`p-2 border rounded cursor-pointer ${
              selectedProvinceId === province.id ? 'bg-blue-200' : 'bg-gray-100'
            }`}
            onClick={() => onProvinceClick(province.id)}
          >
            <div className="font-semibold">{province.name}</div>
            <div className="text-sm text-gray-600">{province.terrain}</div>
            <div className="text-sm">Omistaja: {province.owner}</div>
          </div>
        ))}
      </div>
      <div className="mt-4">
        <h3 className="text-lg font-bold">Armeijat</h3>
        <ul>
          {armies.map((army) => (
            <li
              key={army.id}
              className={`cursor-pointer ${selectedArmyId === army.id ? 'font-bold' : ''}`}
              onClick={() => onArmyClick(army.id)}
            >
              Armeija {army.id} - {army.units.length} yksikköä
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
