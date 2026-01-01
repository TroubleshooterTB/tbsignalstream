import { describe, it, expect, vi, beforeEach } from 'vitest';
import { notify } from '../notifications';
import { toast } from 'sonner';

// Mock sonner
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
}));

describe('notify', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('success', () => {
    it('should call toast.success with correct parameters', () => {
      notify.success('Operation completed');

      expect(toast.success).toHaveBeenCalledWith('Operation completed', {
        description: undefined,
      });
    });

    it('should include description if provided', () => {
      notify.success('Done', 'All tasks completed');

      expect(toast.success).toHaveBeenCalledWith('Done', {
        description: 'All tasks completed',
      });
    });
  });

  describe('error', () => {
    it('should call toast.error with correct parameters', () => {
      notify.error('Something went wrong');

      expect(toast.error).toHaveBeenCalledWith('Something went wrong', {
        description: undefined,
        duration: 10000,
      });
    });

    it('should include description if provided', () => {
      notify.error('Error', 'Failed to connect');

      expect(toast.error).toHaveBeenCalledWith('Error', {
        description: 'Failed to connect',
        duration: 10000,
      });
    });
  });

  describe('warning', () => {
    it('should call toast.warning with correct parameters', () => {
      notify.warning('Please review');

      expect(toast.warning).toHaveBeenCalledWith('Please review', {
        description: undefined,
      });
    });
  });

  describe('info', () => {
    it('should call toast.info with correct parameters', () => {
      notify.info('Information');

      expect(toast.info).toHaveBeenCalledWith('Information', {
        description: undefined,
      });
    });
  });

  describe('botError', () => {
    it('should format bot error message correctly', () => {
      notify.botError('Connection failed');

      expect(toast.error).toHaveBeenCalledWith('❌ Bot Error', {
        description: 'Connection failed',
        duration: 10000,
      });
    });
  });

  describe('botStarted', () => {
    it('should show bot started notification with mode and strategy', () => {
      notify.botStarted('paper', 'Alpha-Ensemble');

      expect(toast.success).toHaveBeenCalledWith('🤖 Bot Started', {
        description: 'Mode: PAPER | Strategy: Alpha-Ensemble',
      });
    });

    it('should handle live mode', () => {
      notify.botStarted('live', 'Ironclad');

      expect(toast.success).toHaveBeenCalledWith('🤖 Bot Started', {
        description: 'Mode: LIVE | Strategy: Ironclad',
      });
    });
  });

  describe('botStopped', () => {
    it('should show bot stopped notification', () => {
      notify.botStopped();

      expect(toast.info).toHaveBeenCalledWith('Bot Stopped', {
        description: 'Trading bot has been stopped',
      });
    });
  });

  describe('wsConnected', () => {
    it('should show WebSocket connected notification', () => {
      notify.wsConnected();

      expect(toast.success).toHaveBeenCalledWith('WebSocket Connected', {
        description: 'Live market data streaming active',
      });
    });
  });

  describe('wsDisconnected', () => {
    it('should show WebSocket disconnected info', () => {
      notify.wsDisconnected();

      expect(toast.info).toHaveBeenCalledWith('WebSocket Disconnected', {
        description: 'Live market data stopped',
      });
    });
  });

  describe('marketClosed', () => {
    it('should show market closed notification', () => {
      notify.marketClosed();

      expect(toast.info).toHaveBeenCalledWith('Market Closed', {
        description: 'Trading unavailable outside market hours',
      });
    });
  });
});
