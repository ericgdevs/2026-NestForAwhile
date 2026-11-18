type Nutrition = {
  serving_size_g?: number | null;
  calories?: number | null;
  total_fat_g?: number | null;
  sat_fat_g?: number | null;
  trans_fat_g?: number | null;
  cholesterol_mg?: number | null;
  sodium_mg?: number | null;
  carbs_g?: number | null;
  fiber_g?: number | null;
  sugar_g?: number | null;
  added_sugar_g?: number | null;
  protein_g?: number | null;
  vitamin_d_mcg?: number | null;
  calcium_mg?: number | null;
  iron_mg?: number | null;
  potassium_mg?: number | null;
};

type Row = { key: keyof Nutrition; label: string; unit: string; dv?: number; depth?: 1 | 2; bold?: boolean };

// FDA label order. `dv` is the FDA Daily Value used for the % column; rows without one show no percent.
const MAIN_ROWS: Row[] = [
  { key: "total_fat_g", label: "Total Fat", unit: "g", dv: 78, bold: true },
  { key: "sat_fat_g", label: "Saturated Fat", unit: "g", dv: 20, depth: 1 },
  { key: "trans_fat_g", label: "Trans Fat", unit: "g", depth: 1 },
  { key: "cholesterol_mg", label: "Cholesterol", unit: "mg", dv: 300, bold: true },
  { key: "sodium_mg", label: "Sodium", unit: "mg", dv: 2300, bold: true },
  { key: "carbs_g", label: "Total Carbohydrate", unit: "g", dv: 275, bold: true },
  { key: "fiber_g", label: "Dietary Fiber", unit: "g", dv: 28, depth: 1 },
  { key: "sugar_g", label: "Total Sugars", unit: "g", depth: 1 },
  { key: "added_sugar_g", label: "Includes Added Sugars", unit: "g", dv: 50, depth: 2 },
  { key: "protein_g", label: "Protein", unit: "g", bold: true },
];
const MINERAL_ROWS: Row[] = [
  { key: "vitamin_d_mcg", label: "Vitamin D", unit: "mcg", dv: 20 },
  { key: "calcium_mg", label: "Calcium", unit: "mg", dv: 1300 },
  { key: "iron_mg", label: "Iron", unit: "mg", dv: 18 },
  { key: "potassium_mg", label: "Potassium", unit: "mg", dv: 4700 },
];

function NutrientRows({ facts, rows }: { facts: Nutrition; rows: Row[] }) {
  return (
    <>
      {rows
        .filter((row) => facts[row.key] != null)
        .map(({ key, label, unit, dv, depth, bold }) => (
          <div className={depth ? `nf-sub nf-sub-${depth}` : undefined} key={key}>
            <dt className={bold ? "nf-bold" : undefined}>
              {label} <span className="nf-amt">{facts[key]}{unit}</span>
            </dt>
            <dd>{dv ? `${Math.round(((facts[key] as number) / dv) * 100)}%` : ""}</dd>
          </div>
        ))}
    </>
  );
}

// An FDA-style Nutrition Facts panel, shared by Scan and Cart. Anything with no value is left off.
export default function NutritionFacts({ facts }: { facts: Nutrition }) {
  const hasDv = [...MAIN_ROWS, ...MINERAL_ROWS].some((row) => row.dv && facts[row.key] != null);
  return (
    <div className="nf">
      <h3 className="nf-title">Nutrition Facts</h3>
      {facts.serving_size_g != null && (
        <p className="nf-serving">
          <b>Serving size</b>
          <b>{facts.serving_size_g}g</b>
        </p>
      )}
      <p className="nf-per">Amount per serving</p>
      {facts.calories != null && (
        <div className="nf-cal">
          <span>Calories</span>
          <span>{facts.calories}</span>
        </div>
      )}
      {hasDv && <p className="nf-dvhead">% Daily Value*</p>}
      <dl className="nf-rows">
        <NutrientRows facts={facts} rows={MAIN_ROWS} />
      </dl>
      <dl className="nf-rows nf-minerals">
        <NutrientRows facts={facts} rows={MINERAL_ROWS} />
      </dl>
      {hasDv && (
        <p className="nf-note">
          * The % Daily Value (DV) tells you how much a nutrient in a serving of food contributes to a daily diet. 2,000
          calories a day is used for general nutrition advice.
        </p>
      )}
    </div>
  );
}
