'use client';

import { AngelConnectButton } from '@/components/angel-connect-button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

export default function Settings() {
	return (
		<div className="space-y-6">
			<div>
				<h3 className="text-lg font-medium">Settings</h3>
				<p className="text-sm text-muted-foreground">Manage your account and integrations.</p>
			</div>
			<Separator />
			<Card>
				<CardHeader>
					<CardTitle>Broker Integration</CardTitle>
					<CardDescription>Connect your trading account to enable live trading features.</CardDescription>
				</CardHeader>
				<CardContent>
					<AngelConnectButton />
				</CardContent>
			</Card>
		</div>
	);
}
