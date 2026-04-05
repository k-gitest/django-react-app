import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

/* =========================
   テスト対象
========================= */
import { useUIStore, useExclusiveModal } from '@/hooks/use-exclusive-modal';

/* =========================
   セットアップ
========================= */

// console.warnを抑制（DEV環境のwarningがテスト出力に混入するのを防ぐ）
vi.spyOn(console, 'warn').mockImplementation(() => { });

/* =========================
   テスト本体
========================= */

describe('useUIStore', () => {
  // Zustandはモジュール間で状態が共有されるので各テスト前にリセット
  beforeEach(() => {
    useUIStore.setState({ currentModalId: null });
    vi.clearAllMocks();
  });

  /* --------------------
     初期状態
  -------------------- */

  describe('初期状態', () => {
    it('currentModalIdはnull', () => {
      const { currentModalId } = useUIStore.getState();
      expect(currentModalId).toBeNull();
    });
  });

  /* --------------------
     openModal
  -------------------- */

  describe('openModal', () => {
    it('他のモーダルが開いていないとき trueを返しcurrentModalIdを設定する', () => {
      const { openModal } = useUIStore.getState();

      const result = openModal('modal-a');

      expect(result).toBe(true);
      expect(useUIStore.getState().currentModalId).toBe('modal-a');
    });

    it('既に他のモーダルが開いているとき falseを返しcurrentModalIdは変わらない', () => {
      useUIStore.setState({ currentModalId: 'modal-a' });
      const { openModal } = useUIStore.getState();

      const result = openModal('modal-b');

      expect(result).toBe(false);
      expect(useUIStore.getState().currentModalId).toBe('modal-a');
    });

    it('自分自身と同じIDで再度openしようとしたとき falseを返す', () => {
      useUIStore.setState({ currentModalId: 'modal-a' });
      const { openModal } = useUIStore.getState();

      const result = openModal('modal-a');

      expect(result).toBe(false);
    });
  });

  /* --------------------
     closeModal
  -------------------- */

  describe('closeModal', () => {
    it('現在開いているIDと一致するとき currentModalIdをnullにする', () => {
      useUIStore.setState({ currentModalId: 'modal-a' });
      const { closeModal } = useUIStore.getState();

      closeModal('modal-a');

      expect(useUIStore.getState().currentModalId).toBeNull();
    });

    it('現在開いているIDと異なるIDで閉じようとしたとき 状態は変わらない', () => {
      useUIStore.setState({ currentModalId: 'modal-a' });
      const { closeModal } = useUIStore.getState();

      closeModal('modal-b');

      // modal-aは開いたまま
      expect(useUIStore.getState().currentModalId).toBe('modal-a');
    });

    it('モーダルが開いていないとき closeしても状態はnullのまま', () => {
      const { closeModal } = useUIStore.getState();

      closeModal('modal-a');

      expect(useUIStore.getState().currentModalId).toBeNull();
    });
  });

  /* --------------------
     排他制御の連続操作
  -------------------- */

  describe('排他制御の連続操作', () => {
    it('openしてcloseすると再びopenできる', () => {
      const { openModal, closeModal } = useUIStore.getState();

      openModal('modal-a');
      closeModal('modal-a');

      const result = openModal('modal-b');
      expect(result).toBe(true);
      expect(useUIStore.getState().currentModalId).toBe('modal-b');
    });

    it('modal-aを閉じた後にmodal-bを開ける', () => {
      const { openModal, closeModal } = useUIStore.getState();

      expect(openModal('modal-a')).toBe(true);
      expect(openModal('modal-b')).toBe(false); // ブロックされる

      closeModal('modal-a');

      expect(openModal('modal-b')).toBe(true);
      expect(useUIStore.getState().currentModalId).toBe('modal-b');
    });
  });
});

/* =========================
   useExclusiveModal
========================= */

describe('useExclusiveModal', () => {
  beforeEach(() => {
    // Zustandの状態をリセット
    useUIStore.setState({ currentModalId: null });
    vi.clearAllMocks();
  });

  afterEach(() => {
    // テスト後もリセット（アンマウントのuseEffectが残る場合があるため）
    useUIStore.setState({ currentModalId: null });
  });

  /* --------------------
     初期状態
  -------------------- */

  describe('初期状態', () => {
    it('isOpenはfalse', () => {
      const { result } = renderHook(() => useExclusiveModal());

      expect(result.current.isOpen).toBe(false);
    });

    it('open・closeが関数として返る', () => {
      const { result } = renderHook(() => useExclusiveModal());

      expect(typeof result.current.open).toBe('function');
      expect(typeof result.current.close).toBe('function');
    });
  });

  /* --------------------
     open
  -------------------- */

  describe('open', () => {
    it('openするとisOpenがtrueになる', () => {
      const { result } = renderHook(() => useExclusiveModal());

      act(() => {
        result.current.open();
      });

      expect(result.current.isOpen).toBe(true);
    });

    it('openはtrueを返す（成功時）', () => {
      const { result } = renderHook(() => useExclusiveModal());

      let returnValue: boolean | undefined;
      act(() => {
        returnValue = result.current.open();
      });

      expect(returnValue).toBe(true);
    });

    it('他のモーダルが開いているとき isOpenはfalseのままでfalseを返す', () => {
      // 先に別のモーダルを開いておく
      useUIStore.setState({ currentModalId: 'other-modal' });

      const { result } = renderHook(() => useExclusiveModal());

      let returnValue: boolean | undefined;
      act(() => {
        returnValue = result.current.open();
      });

      expect(returnValue).toBe(false);
      expect(result.current.isOpen).toBe(false);
    });
  });

  /* --------------------
     close
  -------------------- */

  describe('close', () => {
    it('openした後にcloseするとisOpenがfalseになる', () => {
      const { result } = renderHook(() => useExclusiveModal());

      act(() => { result.current.open(); });
      act(() => { result.current.close(); });

      expect(result.current.isOpen).toBe(false);
    });

    it('closeするとcurrentModalIdがnullになる', () => {
      const { result } = renderHook(() => useExclusiveModal());

      act(() => { result.current.open(); });

      expect(useUIStore.getState().currentModalId).not.toBeNull();

      act(() => { result.current.close(); });

      expect(useUIStore.getState().currentModalId).toBeNull();
    });

    it('openせずにcloseしても isOpenはfalseのまま', () => {
      const { result } = renderHook(() => useExclusiveModal());

      act(() => { result.current.close(); });

      expect(result.current.isOpen).toBe(false);
    });
  });

  /* --------------------
     open→close→openのサイクル
  -------------------- */

  describe('open→close→openのサイクル', () => {
    it('closeした後に再度openできる', () => {
      const { result } = renderHook(() => useExclusiveModal());

      act(() => { result.current.open(); });
      act(() => { result.current.close(); });
      act(() => { result.current.open(); });

      expect(result.current.isOpen).toBe(true);
    });

    it('2つのフックが独立したIDを持ち 片方しか開けない', () => {
      const { result: resultA } = renderHook(() => useExclusiveModal());
      const { result: resultB } = renderHook(() => useExclusiveModal());

      // AをOpenすると成功
      act(() => { resultA.current.open(); });
      expect(resultA.current.isOpen).toBe(true);

      // BはAが開いているのでブロックされる
      act(() => { resultB.current.open(); });
      expect(resultB.current.isOpen).toBe(false);

      // AをCloseするとBが開ける
      act(() => { resultA.current.close(); });
      act(() => { resultB.current.open(); });
      expect(resultB.current.isOpen).toBe(true);
    });
  });

  /* --------------------
     アンマウント時のクリーンアップ
  -------------------- */

  describe('アンマウント時のクリーンアップ（useEffect cleanup）', () => {
    it('アンマウント時にcurrentModalIdがnullにリセットされる', () => {
      const { result, unmount } = renderHook(() => useExclusiveModal());

      // モーダルを開く
      act(() => { result.current.open(); });
      expect(useUIStore.getState().currentModalId).not.toBeNull();

      // アンマウント → useEffectのcleanupが走る
      unmount();

      expect(useUIStore.getState().currentModalId).toBeNull();
    });

    it('アンマウント後に別のモーダルが開ける', () => {
      const { result: resultA, unmount } = renderHook(() => useExclusiveModal());
      const { result: resultB } = renderHook(() => useExclusiveModal());

      act(() => { resultA.current.open(); });
      expect(resultA.current.isOpen).toBe(true);

      // AをアンマウントするとBが開ける
      unmount();

      act(() => { resultB.current.open(); });
      expect(resultB.current.isOpen).toBe(true);
    });

    it('開いていないままアンマウントしても エラーが発生しない', () => {
      const { unmount } = renderHook(() => useExclusiveModal());

      // isOpenがfalseのままアンマウント
      expect(() => unmount()).not.toThrow();
      expect(useUIStore.getState().currentModalId).toBeNull();
    });
  });
});