export class BudgetError extends Error {
  readonly reason: string;
  constructor(reason: string) {
    super(reason);
    this.reason = reason;
  }
}

export async function searchLambda(_f: number, _b: number, _m: (l: number) => Promise<number>, _max?: number): Promise<never> {
  throw new BudgetError("not implemented");
}

export function violatesMonotonicity(_s: { lambda: number; duration: number }[]): boolean {
  throw new BudgetError("not implemented");
}
