import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface AuthButtonProps {
  label: string;
  description: string;
  onAuth: () => void;
  isLoading: boolean;
}

export function AuthButton({ label, description, onAuth, isLoading }: AuthButtonProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">{label}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button 
            onClick={onAuth} 
            className="w-full" 
            size="lg"
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : label}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}