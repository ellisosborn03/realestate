const { calculateDistressScore } = require('../src/services/calculateDistressScore');

describe('Distress Score Engine', () => {
  test('High distress case (4331 122ND DR N)', () => {
    const input = {
      loanToValuePct: 0.94,
      daysOnMarket: 88,
      medianDaysOnMarket: 33,
      originalListPrice: 500000,
      currentListPrice: 435000,
      preforeclosureActive: true,
      taxDelinquent: true,
      absenteeOwner: true,
      absorptionRate: 6.8
    };
    console.log('TEST: High distress case input:', input);
    const result = calculateDistressScore(input);
    console.log('TEST: High distress case output:', result);
    expect(result.distress_score).toBeGreaterThan(85);
    expect(result.estimated_discount).toBe("15–20%+");
  });

  test('Low distress case (456 Ocean Dr)', () => {
    const input = {
      loanToValuePct: 0.45,
      daysOnMarket: 12,
      medianDaysOnMarket: 29,
      originalListPrice: 650000,
      currentListPrice: 645000,
      preforeclosureActive: false,
      taxDelinquent: false,
      absenteeOwner: false,
      absorptionRate: 2.5
    };
    console.log('TEST: Low distress case input:', input);
    const result = calculateDistressScore(input);
    console.log('TEST: Low distress case output:', result);
    expect(result.distress_score).toBeLessThan(25);
    expect(result.estimated_discount).toBe("0–2%");
  });

  test('Mid distress case (216 Alhambra Pl)', () => {
    const input = {
      loanToValuePct: 0.78,
      daysOnMarket: 44,
      medianDaysOnMarket: 35,
      originalListPrice: 490000,
      currentListPrice: 470000,
      preforeclosureActive: false,
      taxDelinquent: true,
      absenteeOwner: false,
      absorptionRate: 5.2
    };
    console.log('TEST: Mid distress case input:', input);
    const result = calculateDistressScore(input);
    console.log('TEST: Mid distress case output:', result);
    expect(result.distress_score).toBeGreaterThanOrEqual(55);
    expect(result.distress_score).toBeLessThanOrEqual(65);
    expect(result.estimated_discount).toBe("3–9%");
  });

  test('Preforeclosure spike only (817 Greenbriar Dr)', () => {
    const input = {
      loanToValuePct: 0.60,
      daysOnMarket: 22,
      medianDaysOnMarket: 28,
      originalListPrice: 470000,
      currentListPrice: 470000,
      preforeclosureActive: true,
      taxDelinquent: false,
      absenteeOwner: false,
      absorptionRate: 3.9
    };
    console.log('TEST: Preforeclosure spike input:', input);
    const result = calculateDistressScore(input);
    console.log('TEST: Preforeclosure spike output:', result);
    expect(result.distress_score).toBeGreaterThan(60);
    expect(result.estimated_discount).toBe("10–15%");
  });

  test('Edge case: missing price drop, high DOM', () => {
    const input = {
      loanToValuePct: 0.88,
      daysOnMarket: 120,
      medianDaysOnMarket: 40,
      originalListPrice: 480000,
      currentListPrice: 480000,
      preforeclosureActive: false,
      taxDelinquent: false,
      absenteeOwner: true,
      absorptionRate: 7.0
    };
    console.log('TEST: Edge case input:', input);
    const result = calculateDistressScore(input);
    console.log('TEST: Edge case output:', result);
    expect(result.distress_score).toBeGreaterThanOrEqual(70);
    expect(result.distress_score).toBeLessThanOrEqual(80);
    expect(result.estimated_discount).toBe("10–15%");
  });
}); 