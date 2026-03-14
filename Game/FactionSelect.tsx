/**
 * FactionSelect.tsx — Heimonvalintanäkymä (vanha heksilauta-versio)
 *
 * Näyttää 4 heimoa (mongoli, Kiina, Persia, Venäjä) kortteina
 * aloitusjoukkoineen ja voittoehtojen kera. Käytetään MongolianGame-komponentissa.
 */
import { FactionId, FACTIONS, AI_PERSONALITIES } from '@/types/game';
import { FACTION_DATA_1206 } from '@/types/province';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Crown, Swords, Shield, Users, Coins, TreePine, Castle, Compass, Sword } from 'lucide-react';

interface ProvinceFactionSelectProps {
  onSelect: (factionId: FactionId) => void;
}

interface FactionSelectProps {
  onSelect: (faction: FactionId) => void;
}

const factionIcons: Record<FactionId, React.ReactNode> = {
  mongol: <Compass className="w-10 h-10" />,
  china: <Castle className="w-10 h-10" />,
  persia: <Coins className="w-10 h-10" />,
  russia: <TreePine className="w-10 h-10" />,
};

const factionBackgrounds: Record<FactionId, string> = {
  mongol: 'from-amber-900/90 to-amber-950/90',
  china: 'from-red-900/90 to-red-950/90',
  persia: 'from-blue-900/90 to-blue-950/90',
  russia: 'from-green-900/90 to-green-950/90',
};

export const FactionSelect = ({ onSelect }: FactionSelectProps) => {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center p-4">
      {/* Title with dramatic styling */}
      <div className="text-center mb-12">
        <div className="relative inline-block">
          <h1 className="text-5xl md:text-7xl font-display font-bold text-transparent bg-clip-text bg-gradient-to-b from-amber-200 via-amber-400 to-amber-600 mb-2">
            Mongolien Valtakunta
          </h1>
          <div className="absolute -inset-1 bg-gradient-to-r from-amber-600/20 via-transparent to-amber-600/20 blur-xl -z-10" />
        </div>
        <p className="text-xl text-amber-200/80 max-w-2xl mx-auto mt-4">
          Valitse heimosi ja johda sitä valloittamaan Silkkitie
        </p>
        <div className="flex items-center justify-center gap-4 mt-4 text-amber-300/60 text-sm">
          <span>⚔️ Strategiapeli</span>
          <span>•</span>
          <span>🎲 30 vuoroa</span>
          <span>•</span>
          <span>🏆 4 voittotietä</span>
        </div>
      </div>
      
      {/* Faction cards */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl w-full">
        {(Object.entries(FACTIONS) as [FactionId, typeof FACTIONS[FactionId]][]).map(([id, faction]) => {
          const personality = AI_PERSONALITIES[id === 'mongol' ? 'aggressive' : id === 'china' ? 'defensive' : id === 'persia' ? 'economic' : 'balanced'];
          
          return (
            <Card 
              key={id}
              className={`relative overflow-hidden bg-gradient-to-br ${factionBackgrounds[id]} border-2 hover:scale-105 transition-all duration-300 cursor-pointer group`}
              style={{ borderColor: `${faction.color}66` }}
              onClick={() => onSelect(id)}
            >
              {/* Glow effect on hover */}
              <div 
                className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                style={{ 
                  background: `radial-gradient(ellipse at center, ${faction.color}22 0%, transparent 70%)`,
                }}
              />
              
              {/* Top color bar */}
              <div 
                className="absolute top-0 left-0 right-0 h-1 group-hover:h-2 transition-all"
                style={{ backgroundColor: faction.color }}
              />
              
              <CardHeader className="text-center pt-8 relative">
                {/* Faction icon */}
                <div 
                  className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg group-hover:scale-110 transition-transform"
                  style={{ 
                    backgroundColor: faction.color,
                    boxShadow: `0 0 30px ${faction.color}66`,
                  }}
                >
                  <span className="text-white">{factionIcons[id]}</span>
                </div>
                
                <CardTitle className="text-2xl text-white">{faction.name}</CardTitle>
                <CardDescription className="text-lg" style={{ color: `${faction.color}cc` }}>
                  {faction.bonus}
                </CardDescription>
              </CardHeader>
              
              <CardContent className="text-center pb-8 relative">
                <p className="text-sm text-white/60 mb-6 min-h-[3rem]">
                  {faction.bonusDescription}
                </p>
                
                {/* Starting info */}
                <div className="border-t border-white/10 pt-4 mb-6">
                  <p className="text-xs text-white/40 mb-3 uppercase tracking-wide">Aloitusjoukot</p>
                  <div className="flex justify-center gap-4 text-white/70">
                    <div className="text-center">
                      <span className="text-2xl">🐎</span>
                      <p className="text-xs">×3</p>
                    </div>
                    <div className="text-center">
                      <span className="text-2xl">⚔️</span>
                      <p className="text-xs">×2</p>
                    </div>
                    <div className="text-center">
                      <span className="text-2xl">👑</span>
                      <p className="text-xs">×1</p>
                    </div>
                  </div>
                </div>
                
                <Button 
                  className="w-full font-bold text-lg py-6 shadow-xl group-hover:shadow-2xl transition-all"
                  style={{ 
                    backgroundColor: faction.color,
                    color: 'white',
                  }}
                >
                  <Crown className="w-5 h-5 mr-2" />
                  Valitse
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
      
      {/* Instructions */}
      <div className="mt-12 text-center text-amber-200/50 text-sm max-w-2xl">
        <p className="mb-2">
          <strong>Voittoehdot:</strong> Valloita 60% kaupungeista (sotilaallinen), kerää 50 pistettä ja 5 kauppareittiä (taloudellinen), tai eliminoi kaikki vastustajat.
        </p>
        <p>
          Peli on vuoropohjainen strategiapeli jossa johdat heimoasi valloittamaan Aasian stepin.
        </p>
      </div>
    </div>
  );
};

export const ProvinceFactionSelect = ({ onSelect }: ProvinceFactionSelectProps) => {
  const factions = Object.values(FACTION_DATA_1206);
  
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-gradient-to-br from-slate-950 via-amber-950/20 to-slate-950 p-4 overflow-auto">
      {/* Background effects */}
      <div 
        className="absolute inset-0 opacity-30"
        style={{
          background: `radial-gradient(ellipse at 30% 20%, rgba(251, 191, 36, 0.15) 0%, transparent 50%),
                       radial-gradient(ellipse at 70% 80%, rgba(180, 83, 9, 0.1) 0%, transparent 50%)`,
        }}
      />
      
      <div className="relative z-10 max-w-5xl w-full">
        {/* Title */}
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-display font-bold text-amber-100 mb-2">
            Mongolien Valtakunta
          </h1>
          <p className="text-amber-200/60 text-lg">
            Vuosi 1206 — Valitse valtakuntasi
          </p>
        </div>
        
        {/* Faction grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {factions.map(faction => {
            // Faction-specific stats
            const stats = {
              mongol: { cavalry: 5, economy: 2, defense: 2 },
              jin: { cavalry: 2, economy: 4, defense: 5 },
              song: { cavalry: 1, economy: 5, defense: 3 },
              xixia: { cavalry: 3, economy: 3, defense: 3 },
              khwarezm: { cavalry: 3, economy: 4, defense: 3 },
              rus: { cavalry: 2, economy: 3, defense: 4 },
              kipchak: { cavalry: 4, economy: 2, defense: 2 },
            }[faction.id];
            
            const difficulty = {
              mongol: 'Keskitaso',
              jin: 'Helppo',
              song: 'Helppo',
              xixia: 'Vaikea',
              khwarezm: 'Keskitaso',
              rus: 'Vaikea',
              kipchak: 'Erittäin vaikea',
            }[faction.id];
            
            const difficultyColor = {
              mongol: 'bg-amber-600',
              jin: 'bg-green-600',
              song: 'bg-green-600',
              xixia: 'bg-orange-600',
              khwarezm: 'bg-amber-600',
              rus: 'bg-orange-600',
              kipchak: 'bg-red-600',
            }[faction.id];
            
            return (
              <Card 
                key={faction.id}
                className="bg-slate-900/80 border-2 transition-all duration-300 hover:scale-[1.02] cursor-pointer group"
                style={{ borderColor: `${faction.color}40` }}
                onClick={() => onSelect(faction.id)}
              >
                <CardContent className="p-4">
                  {/* Header */}
                  <div className="flex items-center gap-3 mb-4">
                    <div 
                      className="w-12 h-12 rounded-full shadow-lg flex items-center justify-center group-hover:scale-110 transition-transform"
                      style={{ 
                        backgroundColor: faction.color,
                        boxShadow: `0 0 20px ${faction.color}50`,
                      }}
                    >
                      <Crown className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-amber-100">{faction.name}</h3>
                      <p className="text-sm text-stone-400">{faction.ruler}</p>
                    </div>
                    <Badge className={difficultyColor}>{difficulty}</Badge>
                  </div>
                  
                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-2 mb-4">
                    <div className="bg-stone-800/50 rounded-lg p-2 text-center">
                      <Sword className="w-4 h-4 text-red-400 mx-auto mb-1" />
                      <div className="flex justify-center gap-0.5">
                        {[...Array(5)].map((_, i) => (
                          <div 
                            key={i}
                            className={`w-2 h-2 rounded-full ${i < stats.cavalry ? 'bg-red-400' : 'bg-stone-700'}`}
                          />
                        ))}
                      </div>
                      <div className="text-[10px] text-stone-500 mt-1">Ratsuväki</div>
                    </div>
                    <div className="bg-stone-800/50 rounded-lg p-2 text-center">
                      <Coins className="w-4 h-4 text-amber-400 mx-auto mb-1" />
                      <div className="flex justify-center gap-0.5">
                        {[...Array(5)].map((_, i) => (
                          <div 
                            key={i}
                            className={`w-2 h-2 rounded-full ${i < stats.economy ? 'bg-amber-400' : 'bg-stone-700'}`}
                          />
                        ))}
                      </div>
                      <div className="text-[10px] text-stone-500 mt-1">Talous</div>
                    </div>
                    <div className="bg-stone-800/50 rounded-lg p-2 text-center">
                      <Shield className="w-4 h-4 text-blue-400 mx-auto mb-1" />
                      <div className="flex justify-center gap-0.5">
                        {[...Array(5)].map((_, i) => (
                          <div 
                            key={i}
                            className={`w-2 h-2 rounded-full ${i < stats.defense ? 'bg-blue-400' : 'bg-stone-700'}`}
                          />
                        ))}
                      </div>
                      <div className="text-[10px] text-stone-500 mt-1">Puolustus</div>
                    </div>
                  </div>
                  
                  {/* Bonus */}
                  <div className="bg-stone-800/30 rounded-lg p-3 text-sm">
                    <div className="text-amber-400 font-semibold mb-1">Erityiskyky:</div>
                    <div className="text-stone-300 text-xs">
                      {faction.id === 'mongol' && '🐴 +30% ratsuväen hyökkäys, nopea liike'}
                      {faction.id === 'jin' && '🏯 +20% verot, vahvat linnoitukset'}
                      {faction.id === 'song' && '💰 +30% verot, vahva talous'}
                      {faction.id === 'xixia' && '⚖️ Tasapainoinen, +10% kaikki'}
                      {faction.id === 'khwarezm' && '🛤️ +20% Silkkitien tulot'}
                      {faction.id === 'rus' && '❄️ +10% puolustus, metsäbonus'}
                      {faction.id === 'kipchak' && '🐎 +20% ratsuväki, nopea liike'}
                    </div>
                  </div>
                  
                  {/* Starting resources */}
                  <div className="flex justify-center gap-4 mt-4 text-xs text-stone-400">
                    <span>💰 {faction.treasury}</span>
                    <span>👥 {faction.manpower}</span>
                    <span>🐴 {faction.horses}</span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
        
        {/* Info */}
        <div className="text-center mt-8 text-stone-500 text-sm">
          <p>Klikkaa valtakuntaa aloittaaksesi pelin</p>
        </div>
      </div>
    </div>
  );
};
