/**
 * Factions.tsx — Heimojen yleiskatsaus
 *
 * Näyttää 4 heimon perustiedot: nimi, bonus ja alkuasetelma.
 * Tiivistetympi versio kuin DetailedFactions.
 */
import { ComicPanel } from "@/components/ComicPanel";

const factions = [
  {
    name: "Mongoli-heimo",
    color: "bg-amber-500",
    bonus: "Ratsuväen bonus, nopea liikkeelläolo",
    startUnits: ["3 ratsuväkiyksikköä", "2 jalkaväkiyksikköä", "1 heimopäällikkö"],
  },
  {
    name: "Kiinan dynastia",
    color: "bg-red-500",
    bonus: "Linnoitukset, teknologia-edistykset",
    startUnits: ["3 ratsuväkiyksikköä", "2 jalkaväkiyksikköä", "1 heimopäällikkö"],
  },
  {
    name: "Persialainen valtakunta",
    color: "bg-blue-500",
    bonus: "Kauppataidot, kulttuuriresurssit",
    startUnits: ["3 ratsuväkiyksikköä", "2 jalkaväkiyksikköä", "1 heimopäällikkö"],
  },
  {
    name: "Venäläiset ruhtinaskunnat",
    color: "bg-green-500",
    bonus: "Talvisotataktiikat, metsäresurssit",
    startUnits: ["3 ratsuväkiyksikköä", "2 jalkaväkiyksikköä", "1 heimopäällikkö"],
  },
];

export const Factions = () => {
  return (
    <section className="py-16">
      <div className="container mx-auto px-4">
        <h2 className="font-display text-3xl font-bold text-center mb-4">
          Heimot ja Faktiot
        </h2>
        <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
          Valitse heimosi ja hyödynnä sen ainutlaatuisia erikoisuuksia
        </p>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {factions.map((faction) => (
            <ComicPanel key={faction.name} className="relative overflow-hidden">
              <div className={`absolute top-0 left-0 right-0 h-2 ${faction.color}`} />
              <div className="pt-4">
                <h3 className="font-display text-lg font-bold mb-2">{faction.name}</h3>
                <p className="text-sm text-accent font-medium mb-4">{faction.bonus}</p>
                
                <div className="border-t border-border pt-3 mt-3">
                  <p className="text-xs font-semibold text-muted-foreground mb-2">ALKUSETUP:</p>
                  <ul className="text-xs text-muted-foreground space-y-1">
                    {faction.startUnits.map((unit, i) => (
                      <li key={i}>• {unit}</li>
                    ))}
                    <li>• 5 satunnaista resurssikorttia</li>
                    <li>• 2 strategiakorttia</li>
                  </ul>
                </div>
              </div>
            </ComicPanel>
          ))}
        </div>
      </div>
    </section>
  );
};

export const DetailedFactions = () => {
  return (
    <section className="py-16">
      <div className="container mx-auto px-4">
        <h2 className="font-display text-3xl font-bold text-center mb-4">
          Heimot ja Faktiot — Yksityiskohtainen Kuvaus
        </h2>
        <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
          Jokainen heimo tarjoaa ainutlaatuisen pelikokemuksen erilaisine vahvuuksineen ja heikkouksineen
        </p>
        
        <div className="max-w-6xl mx-auto space-y-8">
          {factions.map((faction) => (
            <ComicPanel 
              key={faction.name} 
              className="relative overflow-hidden border-l-4 border-amber-500"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500 opacity-5 rounded-full -translate-y-8 translate-x-8" />
              
              <div className="grid lg:grid-cols-3 gap-6">
                {/* Vasen kolumni - Yleiskuvaus */}
                <div>
                  <div className="inline-block px-3 py-1 bg-amber-500 text-white text-xs rounded-full mb-3">
                    {faction.name}
                  </div>
                  <h3 className="font-display text-2xl font-bold mb-3">{faction.name}</h3>
                  <p className="text-sm text-muted-foreground mb-4">{faction.bonus}</p>
                  
                  <div className="bg-secondary/50 p-3 rounded-sm">
                    <p className="text-xs font-semibold text-accent mb-1">PELITYYLI:</p>
                    <p className="text-sm text-muted-foreground italic">Strateginen pelityyli</p>
                  </div>
                </div>
                
                {/* Keskimmäinen kolumni - Vahvuudet & Heikkous */}
                <div>
                  <h4 className="font-display font-bold text-sm text-primary mb-3">VAHVUUDET:</h4>
                  <ul className="space-y-2 mb-4">
                    <li className="flex items-start gap-2 text-sm">
                      <span className="w-4 h-4 text-primary flex-shrink-0 mt-0.5">✓</span>
                      <span className="text-muted-foreground">{faction.bonus}</span>
                    </li>
                  </ul>
                  
                  <div className="flex items-start gap-2 p-3 bg-destructive/10 rounded-sm">
                    <span className="w-4 h-4 text-destructive flex-shrink-0 mt-0.5">⚠</span>
                    <div>
                      <p className="text-xs font-semibold text-destructive mb-1">HEIKKOUS:</p>
                      <p className="text-sm text-muted-foreground">Ei erityisiä heikkouksia</p>
                    </div>
                  </div>
                </div>
                
                {/* Oikea kolumni - Erikoiskyky & Aloitus */}
                <div>
                  <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-sm mb-4">
                    <p className="text-xs font-semibold text-accent mb-1">ERIKOISKYKY:</p>
                    <h4 className="font-display font-bold text-sm mb-1">Erikoiskyky</h4>
                    <p className="text-xs text-muted-foreground">{faction.bonus}</p>
                  </div>
                  
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground mb-2">ALKUASETELMA:</p>
                    <ul className="text-xs text-muted-foreground space-y-1">
                      {faction.startUnits.map((unit, i) => (
                        <li key={i}>• {unit}</li>
                      ))}
                      <li className="mt-2">📦 Resurssit</li>
                      <li>📍 Alue</li>
                    </ul>
                  </div>
                </div>
              </div>
            </ComicPanel>
          ))}
        </div>
      </div>
    </section>
  );
};
