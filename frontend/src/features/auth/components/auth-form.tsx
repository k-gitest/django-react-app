import { FormInput, FormWrapper } from '@/components/form/form-parts';
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
    if (props.type === 'login') {
      signIn(formData);
    } else {
      signUp(formData);
    }

    form.reset();
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="w-full flex flex-col gap-2 items-center">
        <FormWrapper onSubmit={handleSubmit} form={form}>
          <FormInput label="email" name="email" placeholder="emailを入力してください" />
          <FormInput label="password" name="password" placeholder="パスワードを入力してください" />
          <div className="text-center">
            <Button type="submit" className="w-32" disabled={signInMutation.isPending || signUpMutation.isPending}>
              {(signInMutation.isPending || signUpMutation.isPending) && <Loader className="animate-spin" />} 送信
            </Button>
          </div>
        </FormWrapper>
      </div>
    </div>
  );
};
