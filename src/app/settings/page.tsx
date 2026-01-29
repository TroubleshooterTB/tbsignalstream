'use client';

import { useState, useEffect } from 'react';
import { AngelConnectButton } from '@/components/angel-connect-button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Copy, Check, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { getUserSettings, updateUserSettings, testTelegramNotification, getWebhookUrl, type UserSettings } from '@/lib/api/settings';
import { getScreeningModes, setScreeningMode, type ScreeningMode } from '@/lib/api/screening';

export default function Settings() {
	const [userId] = useState('default_user'); // TODO: Get from auth context
	const [settings, setSettings] = useState<UserSettings | null>(null);
	const [screeningModes, setScreeningModes] = useState<ScreeningMode[]>([]);
	const [loading, setLoading] = useState(true);
	const [saving, setSaving] = useState(false);
	const [testingTelegram, setTestingTelegram] = useState(false);
	const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
	const [telegramTestResult, setTelegramTestResult] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
	const [copiedWebhook, setCopiedWebhook] = useState(false);

	// Load settings and screening modes
	useEffect(() => {
		console.log('Settings page: Loading data...');
		Promise.all([
			getUserSettings(userId).catch(err => {
				console.error('Failed to load user settings:', err);
				// Return default settings if API fails
				return {
					user_id: userId,
					screening_mode: 'RELAXED' as const,
					telegram_enabled: false,
					telegram_bot_token: '',
					telegram_chat_id: '',
					tradingview_webhook_secret: '',
					tradingview_bypass_screening: false
				};
			}),
			getScreeningModes().catch(err => {
				console.error('Failed to load screening modes:', err);
				// Return default modes if API fails
				return [
					{ name: 'RELAXED' as const, description: 'Fewer checks, more signals', expected_signals_per_day: 15, expected_pass_rate: 0.40 },
					{ name: 'MEDIUM' as const, description: 'Balanced approach', expected_signals_per_day: 8, expected_pass_rate: 0.25 },
					{ name: 'STRICT' as const, description: 'Maximum quality filter', expected_signals_per_day: 3, expected_pass_rate: 0.10 }
				];
			})
		]).then(([userSettings, modes]) => {
			console.log('Settings page: Data loaded', { userSettings, modes });
			setSettings(userSettings);
			setScreeningModes(modes);
			setLoading(false);
		}).catch(error => {
			console.error('Failed to load settings:', error);
			setLoading(false);
		});
	}, [userId]);

	const handleSaveSettings = async () => {
		if (!settings) return;

		setSaving(true);
		setSaveMessage(null);

		try {
			await updateUserSettings(settings);
			setSaveMessage({ type: 'success', text: 'Settings saved successfully!' });
		} catch (error) {
			setSaveMessage({ type: 'error', text: `Failed to save settings: ${error instanceof Error ? error.message : 'Unknown error'}` });
		} finally {
			setSaving(false);
		}
	};

	const handleTestTelegram = async () => {
		if (!settings?.telegram_bot_token || !settings?.telegram_chat_id) {
			setTelegramTestResult({ type: 'error', text: 'Please enter bot token and chat ID first' });
			return;
		}

		setTestingTelegram(true);
		setTelegramTestResult(null);

		try {
			const result = await testTelegramNotification(
				userId,
				settings.telegram_bot_token,
				settings.telegram_chat_id
			);
			setTelegramTestResult({ type: 'success', text: result.message });
		} catch (error) {
			setTelegramTestResult({ type: 'error', text: error instanceof Error ? error.message : 'Failed to send test notification' });
		} finally {
			setTestingTelegram(false);
		}
	};

	const handleScreeningModeChange = async (mode: 'RELAXED' | 'MEDIUM' | 'STRICT') => {
		try {
			await setScreeningMode(userId, mode);
			setSettings(prev => prev ? { ...prev, screening_mode: mode } : null);
			setSaveMessage({ type: 'success', text: `Screening mode changed to ${mode}` });
		} catch (error) {
			setSaveMessage({ type: 'error', text: `Failed to change mode: ${error instanceof Error ? error.message : 'Unknown error'}` });
		}
	};

	const copyWebhookUrl = () => {
		navigator.clipboard.writeText(getWebhookUrl());
		setCopiedWebhook(true);
		setTimeout(() => setCopiedWebhook(false), 2000);
	};

	if (loading) {
		return (
			<div className="container mx-auto p-6">
				<h1 className="text-2xl font-bold mb-4">Settings</h1>
				<div className="flex items-center justify-center h-64">
					<Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
				</div>
			</div>
		);
	}

	if (!settings) return null;

	return (
		<div className="space-y-6">
			<div>
				<h3 className="text-lg font-medium">Settings</h3>
				<p className="text-sm text-muted-foreground">Manage your account and integrations.</p>
			</div>
			<Separator />

			{/* Save Message */}
			{saveMessage && (
				<Alert variant={saveMessage.type === 'error' ? 'destructive' : 'default'}>
					{saveMessage.type === 'success' ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
					<AlertDescription>{saveMessage.text}</AlertDescription>
				</Alert>
			)}

			{/* Broker Integration */}
			<Card>
				<CardHeader>
					<CardTitle>Broker Integration</CardTitle>
					<CardDescription>Connect your trading account to enable live trading features.</CardDescription>
				</CardHeader>
				<CardContent>
					<AngelConnectButton />
				</CardContent>
			</Card>

			{/* Screening Mode */}
			<Card>
				<CardHeader>
					<CardTitle>Screening Mode</CardTitle>
					<CardDescription>Control signal quality vs quantity. Changes apply immediately to running bot.</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<RadioGroup
						value={settings.screening_mode || 'RELAXED'}
						onValueChange={(value) => handleScreeningModeChange(value as 'RELAXED' | 'MEDIUM' | 'STRICT')}
					>
						{screeningModes.map((mode) => (
							<div key={mode.name} className="flex items-start space-x-3 space-y-0">
								<RadioGroupItem value={mode.name} id={mode.name} />
								<div className="space-y-1 leading-none">
									<Label htmlFor={mode.name} className="font-medium cursor-pointer">
										{mode.name} ({mode.expected_signals_per_day} signals/day)
									</Label>
									<p className="text-sm text-muted-foreground">{mode.description}</p>
									<p className="text-xs text-muted-foreground">
										Pass rate: {mode.expected_pass_rate} | Max position: {mode.risk_level.max_position}
									</p>
								</div>
							</div>
						))}
					</RadioGroup>
				</CardContent>
			</Card>

			{/* Telegram Notifications */}
			<Card>
				<CardHeader>
					<CardTitle>Telegram Notifications</CardTitle>
					<CardDescription>Get instant alerts for trading signals and position updates.</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="flex items-center justify-between">
						<Label htmlFor="telegram-enabled">Enable Telegram Notifications</Label>
						<Switch
							id="telegram-enabled"
							checked={settings.telegram_enabled || false}
							onCheckedChange={(checked) => setSettings({ ...settings, telegram_enabled: checked })}
						/>
					</div>

					{settings.telegram_enabled && (
						<>
							<div className="space-y-2">
								<Label htmlFor="bot-token">Bot Token</Label>
								<Input
									id="bot-token"
									type="password"
									placeholder="123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
									value={settings.telegram_bot_token || ''}
									onChange={(e) => setSettings({ ...settings, telegram_bot_token: e.target.value })}
								/>
								<p className="text-xs text-muted-foreground">
									Get from @BotFather on Telegram. Create a bot with /newbot command.
								</p>
							</div>

							<div className="space-y-2">
								<Label htmlFor="chat-id">Chat ID</Label>
								<Input
									id="chat-id"
									placeholder="123456789"
									value={settings.telegram_chat_id || ''}
									onChange={(e) => setSettings({ ...settings, telegram_chat_id: e.target.value })}
								/>
								<p className="text-xs text-muted-foreground">
									Get from @userinfobot on Telegram. Send any message to get your ID.
								</p>
							</div>

							<Button
								onClick={handleTestTelegram}
								disabled={testingTelegram || !settings.telegram_bot_token || !settings.telegram_chat_id}
								variant="outline"
							>
								{testingTelegram && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
								Send Test Notification
							</Button>

							{telegramTestResult && (
								<Alert variant={telegramTestResult.type === 'error' ? 'destructive' : 'default'}>
									{telegramTestResult.type === 'success' ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
									<AlertDescription>{telegramTestResult.text}</AlertDescription>
								</Alert>
							)}
						</>
					)}
				</CardContent>
			</Card>

			{/* TradingView Integration */}
			<Card>
				<CardHeader>
					<CardTitle>TradingView Webhook</CardTitle>
					<CardDescription>Receive alerts from TradingView and execute trades automatically.</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="flex items-center justify-between">
						<Label htmlFor="tradingview-enabled">Enable TradingView Alerts</Label>
						<Switch
							id="tradingview-enabled"
							checked={settings.tradingview_enabled || false}
							onCheckedChange={(checked) => setSettings({ ...settings, tradingview_enabled: checked })}
						/>
					</div>

					{settings.tradingview_enabled && (
						<>
							<div className="space-y-2">
								<Label>Webhook URL</Label>
								<div className="flex gap-2">
									<Input
										readOnly
										value={getWebhookUrl()}
										className="font-mono text-sm"
									/>
									<Button
										size="icon"
										variant="outline"
										onClick={copyWebhookUrl}
									>
										{copiedWebhook ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
									</Button>
								</div>
								<p className="text-xs text-muted-foreground">
									Use this URL in TradingView alert webhook settings.
								</p>
							</div>

							<div className="space-y-2">
								<Label htmlFor="webhook-secret">Webhook Secret (Optional)</Label>
								<Input
									id="webhook-secret"
									type="password"
									placeholder="mySecret123"
									value={settings.tradingview_webhook_secret || ''}
									onChange={(e) => setSettings({ ...settings, tradingview_webhook_secret: e.target.value })}
								/>
								<p className="text-xs text-muted-foreground">
									HMAC signature validation for security. Leave empty to accept all requests.
								</p>
							</div>

							<div className="flex items-center justify-between">
								<div className="space-y-0.5">
									<Label htmlFor="bypass-screening">Bypass Screening</Label>
									<p className="text-xs text-muted-foreground">Trust TradingView signals without screening checks</p>
								</div>
								<Switch
									id="bypass-screening"
									checked={settings.tradingview_bypass_screening || false}
									onCheckedChange={(checked) => setSettings({ ...settings, tradingview_bypass_screening: checked })}
								/>
							</div>
						</>
					)}
				</CardContent>
			</Card>

			{/* Save Button */}
			<Button onClick={handleSaveSettings} disabled={saving} size="lg">
				{saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
				Save All Settings
			</Button>
		</div>
	);
}
