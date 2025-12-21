import { FormInput, FormWrapper } from '@/components/form/form-parts';
import { FormPasswordInput } from '@/components/form/form-password-input';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/features/auth/hooks/use-auth';
import { validatedAccount } from '@/features/auth/schemas/account-schema';
import type { Account, AccountFormType } from '@/features/auth/types/auth';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader } from 'lucide-react';
import { useForm } from 'react-hook-form';

export const AccountForm = (props: { type: AccountFormType }) => {
  const form = useForm<Account>({
    resolver: zodResolver(validatedAccount),
    defaultValues: { email: '', password: '' },
  });

  const { signUp, signIn, signUpMutation, signInMutation } = useAuth();

  const handleSubmit = async (formData: Account) => {
    try {
      if (props.type === 'login') {
        await signIn(formData);
      } else {
        await signUp(formData);
      }

      // 成功時のみリセット
      form.reset();
    } catch (error) {
      // エラーは useAuth の onError と errorHandler で処理済み
      if (import.meta.env.DEV) {
        console.error('Form submission error:', error);
      }
    }
  };

  // ローディング状態を統合
  const isLoading = signInMutation.isPending || signUpMutation.isPending;

  return (
    <div className="flex flex-col gap-4">
      <div className="w-full flex flex-col gap-2 items-center">
        <FormWrapper onSubmit={handleSubmit} form={form}>
          <FormInput label="email" name="email" placeholder="emailを入力してください" disabled={isLoading} />
          <FormPasswordInput label="password" name="password" disabled={isLoading} placeholder="パスワードを入力してください" />
          <div className="text-center">
            <Button type="submit" className="w-32" disabled={isLoading}>
              {isLoading && <Loader className="mr-2 h-4 w-4 animate-spin" />}
              {props.type === 'login' ? 'ログイン' : '登録'}
            </Button>
          </div>
        </FormWrapper>
      </div>
    </div>
  );
};
