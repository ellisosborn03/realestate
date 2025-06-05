function calculateDistressScore({
  loanToValuePct,
  daysOnMarket,
  medianDaysOnMarket,
  originalListPrice,
  currentListPrice,
  preforeclosureActive,
  taxDelinquent,
  absenteeOwner,
  absorptionRate
}) {
  // LTV score: 1.0 if LTV > 0.9, else scaled
  const ltvScore = loanToValuePct >= 0.9 ? 1.0 : loanToValuePct / 0.9;
  // DOM score: DOM / median DOM, capped at 2
  const domScore = Math.min(daysOnMarket / (medianDaysOnMarket || 1), 2.0);
  // Price reduction score: (original - current) / original
  const priceReductionScore = originalListPrice > 0 ? Math.max((originalListPrice - currentListPrice) / originalListPrice, 0) : 0;
  // Preforeclosure
  const preforeclosureScore = preforeclosureActive ? 1.0 : 0.0;
  // Tax delinquent
  const taxDelinquentScore = taxDelinquent ? 1.0 : 0.0;
  // Absentee
  const absenteeScore = absenteeOwner ? 1.0 : 0.0;
  // Absorption: 1.0 if > 6 months
  const absorptionScore = absorptionRate > 6 ? 1.0 : absorptionRate / 6;

  let distress_score = (
    0.25 * ltvScore +
    0.20 * domScore +
    0.15 * priceReductionScore +
    0.15 * preforeclosureScore +
    0.10 * taxDelinquentScore +
    0.10 * absenteeScore +
    0.05 * absorptionScore
  ) * 100;

  distress_score = Math.round(Math.min(distress_score, 100));

  let estimated_discount;
  if (distress_score < 30) estimated_discount = "0–2%";
  else if (distress_score < 60) estimated_discount = "3–9%";
  else if (distress_score < 80) estimated_discount = "10–15%";
  else estimated_discount = "15–20%+";

  // Build a basic explanation string
  const reasons = [];
  if (ltvScore >= 0.9) reasons.push('High loan-to-value');
  if (domScore > 1.5) reasons.push('Long days on market');
  if (priceReductionScore > 0.08) reasons.push('Significant price reduction');
  if (preforeclosureActive) reasons.push('Preforeclosure');
  if (taxDelinquent) reasons.push('Tax delinquent');
  if (absenteeOwner) reasons.push('Absentee owner');
  if (absorptionScore > 0.8) reasons.push('High absorption rate');
  let distress_reason = reasons.length ? `Main factors: ${reasons.join(', ')}.` : 'No major distress factors detected.';

  return {
    distress_score,
    estimated_discount,
    distress_reason
  };
}

module.exports = { calculateDistressScore }; 