import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Eye, EyeOff } from 'lucide-react';
import { FormInput } from './form-parts';
import type { InputHTMLAttributes } from 'react';

/**
 * パスワード入力フィールド（表示/非表示切り替え付き）
 * 
 * FormInputをベースに、表示切り替えボタンを追加した拡張コンポーネント
 * 
 * @example
 * <FormPasswordInput
 *   label="password"
 *   name="password"
 *   placeholder="パスワードを入力してください"
 *   disabled={isLoading}
 * />
 */
export const FormPasswordInput = ({
  label,
  name,
  ...props
}: { label: string; name: string } & Omit<InputHTMLAttributes<HTMLInputElement>, 'type'>) => {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="relative">
      <FormInput
        label={label}
        name={name}
        type={showPassword ? 'text' : 'password'}
        {...props}
        className="pr-10"
      />
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="absolute right-0 top-7 h-10 px-3 py-2 hover:bg-transparent"
        onClick={() => setShowPassword(!showPassword)}
        disabled={props.disabled}
        tabIndex={-1}
      >
        {showPassword ? (
          <EyeOff className="h-4 w-4 text-muted-foreground" />
        ) : (
          <Eye className="h-4 w-4 text-muted-foreground" />
        )}
        <span className="sr-only">
          {showPassword ? 'パスワードを隠す' : 'パスワードを表示'}
        </span>
      </Button>
    </div>
  );
};