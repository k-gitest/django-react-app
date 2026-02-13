import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { ApiError } from "@/errors/api-error"
import type { FieldValues, Path, UseFormSetError } from "react-hook-form"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 指数バックオフMath.pow(base, exponent)でbaseのexponent乗となる
export const backoff = (base: number, exponent: number, delayTime: number): number => {
  const baseDelay = delayTime * Math.pow(base, exponent);
  const jitter = (Math.random() * delayTime) / 2;
  return baseDelay + jitter;
};

// 遅延待機時間
export const delay = (millisecond: number): Promise<void> => {
  return new Promise((resolve) => setTimeout(() => resolve, millisecond));
};

// 範囲内判定
export const between = (value: number, min: number, max: number): boolean => {
  return value >= min && value <= max;
};

// rhfへのエラー渡し
// RHFのsetErrorにValidationErrorを流し込むだけの関数
export const mapErrorsToForm = <T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>
) => {
  // fetchRelay が投げているのは ApiError クラスのインスタンス
  if (error instanceof ApiError) {
    // 400 (Validation) も 409 (Conflict) も、
    // ApiError の fieldErrors が値を返してくれるならこれだけで OK
    const errors = error.fieldErrors;

    if (errors) {
      Object.entries(errors).forEach(([field, messages]) => {
        setError(field as Path<T>, {
          type: 'server',
          message: messages[0]
        });
      });
    }
  }
};

// Priority型ガード
export function isPriority(value: string): value is 'LOW' | 'MEDIUM' | 'HIGH' {
  return value === 'LOW' || value === 'MEDIUM' || value === 'HIGH';
}

// Progress型ガード
export function isProgress(value: number): value is 0 | 25 | 50 | 75 | 100 {
  return value === 0 || value === 25 || value === 50 || value === 75 || value === 100;
}