# UI 状態管理

## 概要

本プロジェクトでは、UI の状態管理において以下の原則を採用しています：

1. **コンポーネントの自律性**: 各コンポーネントが自分の状態を管理
2. **グローバル状態の最小化**: 本当に必要な場合のみ Zustand を使用
3. **適切な抽象化**: カスタムフックで複雑さを隠蔽

---

## モーダル排他制御

### 背景と課題

React アプリケーションでモーダルを実装する際、以下の問題が発生します：

**理論上の問題**:
- 複数のコンポーネントがそれぞれ `useState` でモーダル状態を管理
- 同時に複数のモーダルが開く可能性がある
- ユーザーが混乱する

**従来のアプローチの問題点**:

| アプローチ | 問題点 |
|----------|--------|
| **親コンポーネントで一元管理** | props drilling、コンポーネントの自律性が失われる |
| **グローバル状態で全て管理** | 過剰な抽象化、保守性の低下 |
| **UI ライブラリに依存** | ライブラリ変更時にリスク、ビジネスロジックの脆弱性 |

### 採用したアプローチ

**ハイブリッド方式**: コンポーネントの自律性を保ちつつ、排他制御のみグローバル化
```typescript
// Zustand でグローバルなロック状態を管理
interface UIState {
  currentModalId: string | null;
  openModal: (id: string) => boolean;
  closeModal: (id: string) => void;
}

// カスタムフックで抽象化
export const useExclusiveModal = () => {
  const modalId = useId();  // React の標準機能
  const [isOpen, setIsOpen] = useState(false);
  
  const open = () => {
    const success = useUIStore.getState().openModal(modalId);
    if (success) setIsOpen(true);
    return success;
  };
  
  const close = () => {
    setIsOpen(false);
    useUIStore.getState().closeModal(modalId);
  };
  
  // アンマウント時に確実にクリーンアップ
  useEffect(() => {
    return () => closeModal(modalId);
  }, [modalId]);
  
  return { isOpen, open, close };
};
```

---

### 設計判断の経緯

#### 1. なぜ `useRef` ではなく `useId` なのか？

**最初の実装**: `useRef(false)` で追跡
```typescript
// ❌ 問題: ref と state が不整合になる可能性
const isOpenRef = useRef(false);
const [isOpen, setIsOpen] = useState(false);
```

**改善後**: `useId()` で ID 生成
```typescript
// ✅ 解決: React 標準の安定した ID
const modalId = useId();
```

**メリット**:
- 再レンダリング間で安定
- ref 不要でシンプル
- 他のモーダルと完全に区別可能

#### 2. なぜストアで ID 管理するのか？

**最初の実装**: `isAnyModalOpen: boolean`
```typescript
// ❌ 問題: 開いていないコンポーネントがロックを解放してしまう
closeModal() {
  set({ isAnyModalOpen: false });
}
```

**改善後**: `currentModalId: string | null`
```typescript
// ✅ 解決: 自分が開いた場合のみ閉じる
closeModal(id: string) {
  if (get().currentModalId === id) {
    set({ currentModalId: null });
  }
}
```

**メリット**:
- 他のモーダルを誤って閉じることが不可能
- デバッグしやすい（どのモーダルが開いているか追跡可能）

---

### 実装パターン

#### パターン1: 基本的な使用
```typescript
export const TodoItemContainer = ({ todo }) => {
  const { isOpen, open, close } = useExclusiveModal();
  
  return (
    <>
      <TodoItem onEdit={open} />
      {isOpen && <TodoEditModal onClose={close} />}
    </>
  );
};
```

#### パターン2: UI フィードバック付き
```typescript
export const TodoItemContainer = ({ todo }) => {
  const { isOpen, open, close } = useExclusiveModal();
  const { updateMutation, deleteMutation } = useTodos();
  
  // 他のモーダルが開いているかチェック
  const isLockedByOther = useUIStore(
    (state) => state.currentModalId !== null && !isOpen
  );
  
  const isDisabled = 
    updateMutation.isPending || 
    deleteMutation.isPending || 
    isLockedByOther;
  
  return (
    <>
      <TodoItem 
        disabled={isDisabled}
        onEdit={open} 
      />
      {isOpen && <TodoEditModal onClose={close} />}
    </>
  );
};
```

---

### トラブルシューティング

#### モーダルが閉じない

**原因**: `close()` が呼ばれていない

**解決策**:
```typescript
// ✅ 必ず onClose で close() を呼ぶ
<Modal onClose={close} />

// ✅ フォーム送信後も close() を呼ぶ
const handleSubmit = async (data) => {
  await updateTodo(data);
  close(); // 忘れずに呼ぶ
};
```

#### 他のモーダルが開けない

**原因**: 前のモーダルがクリーンアップされていない

**確認方法**:
```typescript
// useUIStore の状態を確認
console.log(useUIStore.getState().currentModalId);
// → null でない場合、どこかのモーダルが開きっぱなし
```

**解決策**:
```typescript
// useEffect のクリーンアップが正しく実装されているか確認
useEffect(() => {
  return () => {
    closeModal(modalId); // 必ず実行される
  };
}, [modalId]);
```

---

### ベストプラクティス

1. **エラー時の処理**:
```typescript
const handleSubmit = async (data) => {
  try {
    await updateTodo(data);
    close(); // ✅ 成功時のみ閉じる
  } catch (error) {
    // ❌ エラー時は閉じない（ユーザーの入力を保持）
    console.error(error);
  }
};
```

2. **複数のモーダルを持つコンポーネント**:
```typescript
// ✅ それぞれ独立した useExclusiveModal を使う
const editModal = useExclusiveModal();
const deleteModal = useExclusiveModal();

// どちらか一方しか開けない（グローバルなロック）
<Button onClick={editModal.open}>編集</Button>
<Button onClick={deleteModal.open}>削除</Button>
```

3. **条件付きレンダリング**:
```typescript
// ✅ isOpen が true の時だけレンダリング
{isOpen && <Modal onClose={close} />}

// ❌ open prop で制御しない（メモリリーク）
<Modal open={isOpen} onClose={close} />
```

---

### 将来の拡張

現在はモーダルのみですが、同じパターンを以下にも適用できます：

- **サイドバー**: 複数のサイドバーが同時に開くのを防ぐ
- **ドロワー**: モバイル UI でのドロワー管理
- **フルスクリーンダイアログ**: 設定画面など

**実装例**:
```typescript
// 同じ useUIStore を拡張
interface UIState {
  currentModalId: string | null;
  currentDrawerId: string | null;  // 追加
  openDrawer: (id: string) => boolean;
  closeDrawer: (id: string) => void;
}

// 同じパターンのカスタムフック
export const useExclusiveDrawer = () => {
  // useExclusiveModal と同じ実装
};
```

---

## その他の UI 状態管理

### TanStack Query（サーバー状態）

**用途**: API からのデータ取得、キャッシュ管理
```typescript
const { data: todos } = useQuery({
  queryKey: ['todos'],
  queryFn: todoService.list,
  staleTime: 5 * 60 * 1000,
});
```

### Zustand（グローバルなクライアント状態）

**用途**: 認証情報、テーマ設定など
```typescript
const useAuthStore = create((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));
```

### useState（ローカル状態）

**用途**: フォーム入力、UI の開閉など
```typescript
const [isOpen, setIsOpen] = useState(false);
```

---

### 使い分けガイド

| 状態の種類 | 使用するツール |
|----------|--------------|
| **サーバーから取得したデータ** | TanStack Query |
| **アプリ全体で共有する状態** | Zustand |
| **コンポーネント内の状態** | useState |
| **排他制御が必要な状態** | Zustand + カスタムフック |