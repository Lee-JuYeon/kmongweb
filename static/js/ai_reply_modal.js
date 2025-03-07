/**
 * Reply Modal UI - 자동 답변 모달 UI 처리
 * ReplyViewModel과 MessageViewModel을 사용하여 UI 렌더링 및 이벤트 처리
 */
class AiReplyModal {
    /**
     * ReplyModal 생성자
     * @param {AiReplyViewModel} aiReplyViewModel - 자동 답변 ViewModel
     * @param {MessageViewModel} messageViewModel - 메시지 ViewModel
     */
    constructor(aiReplyViewModel, messageViewModel) {
        // ViewModels
        this.aiReplyViewModel = aiReplyViewModel;
        this.messageViewModel = messageViewModel;
        
        // DOM 요소
        this.modal = document.getElementById("reply-modal");
        this.openButton = document.getElementById("reply-ai-button");
        this.closeButton = document.getElementById("close-reply-modal");
        this.replyItems = document.querySelectorAll(".reply-item");
        this.replyInput = document.getElementById("reply-edittext");
        
        // aiReplyViewModel 옵저버 등록
        this.aiReplyViewModel.addObserver(this._handleReplyDataChanged.bind(this));
        
        // 이벤트 리스너 초기화
        this._initEventListeners();
    }

    /**
     * 이벤트 리스너 초기화
     * @private
     */
    _initEventListeners() {
        // 모달 열기 버튼
        if (this.openButton) {
            this.openButton.addEventListener("click", () => this._handleOpenModal());
        }
        
        // 모달 닫기 버튼
        if (this.closeButton) {
            this.closeButton.addEventListener("click", () => this._handleCloseModal());
        }
        
        // 자동 답변 항목 클릭 이벤트
        if (this.replyItems) {
            this.replyItems.forEach(item => {
                item.addEventListener("click", (event) => this._handleReplyItemClick(item, event));
            });
        }
    }

    /**
     * 모달 열기 버튼 클릭 처리
     * @private
     */
    _handleOpenModal() {
        if (!this.modal) {
            console.error("모달 요소를 찾을 수 없습니다");
            return;
        }
        
        console.log("모달 열기 시도");


        // 현재 선택된 채팅방 정보 가져오기
        const currentChatroom = this.messageViewModel.getCurrentChatroomInfo();
        
        if (!currentChatroom.chatroomId) {
            console.log("채팅방 ID가 없습니다");
            alert("채팅방을 먼저 선택해주세요.");
            return;
        }
        
        // 모달 표시
        this.modal.style.display = "block";
        console.log("모달이 열렸습니다");

        
        // 자동 답변 로딩 시작 (로딩 상태로 UI 업데이트)
        this._updateLoadingState(true);
        
        // GPT 자동 답변 가져오기
        this.aiReplyViewModel.loadGptAnswers(currentChatroom.chatroomId)
            .catch(error => {
                console.error("자동 답변 로드 중 오류:", error);
                alert("자동 답변을 불러오는 데 실패했습니다.");
            });
    }

    /**
     * 모달 닫기 버튼 클릭 처리
     * @private
     */
    _handleCloseModal() {
        if (this.modal) {
            this.modal.style.display = "none";
        }
    }

    /**
     * 자동 답변 항목 클릭 처리
     * @param {HTMLElement} item - 클릭된 답변 항목 요소
     * @param {Event} event - 클릭 이벤트
     * @private
     */
    _handleReplyItemClick(item, event) {
        // 내용 영역만 클릭했을 때 처리
        const contentDiv = item.querySelector(".reply-item-content");
        const type = item.getAttribute("data-type");
        
        // 로딩 중이 아닌 경우에만 처리
        if (contentDiv && !this.aiReplyViewModel.isLoading) {
            const text = this.aiReplyViewModel.getReply(type);
            
            // 유효한 답변이 있는 경우에만 적용
            if (text && text !== "로딩 중..." && text !== "답변을 불러오는 데 실패했습니다.") {
                if (this.replyInput) {
                    this.replyInput.value = text;
                    this._handleCloseModal();
                }
            }
        }
    }

    /**
     * aiReplyViewModel 데이터 변경 시 호출되는 콜백 (옵저버)
     * @param {Object} data - 변경된 데이터 객체
     * @private
     */
    _handleReplyDataChanged(data) {
        const { replies, isLoading } = data;
        
        // 로딩 상태 업데이트
        this._updateLoadingState(isLoading);
        
        // 각 답변 항목 내용 업데이트
        if (this.replyItems) {
            this.replyItems.forEach(item => {
                const type = item.getAttribute("data-type");
                const contentDiv = item.querySelector(".reply-item-content");
                
                if (contentDiv && type && replies[type]) {
                    contentDiv.textContent = replies[type];
                }
            });
        }
    }

    /**
     * 로딩 상태에 따라 UI 업데이트
     * @param {boolean} isLoading - 로딩 중 여부
     * @private
     */
    _updateLoadingState(isLoading) {
        if (!this.replyItems) return;
        
        if (isLoading) {
            // 모든 항목을 로딩 중 상태로 표시
            this.replyItems.forEach(item => {
                const contentDiv = item.querySelector(".reply-item-content");
                if (contentDiv) {
                    contentDiv.textContent = "로딩 중...";
                }
            });
        }
    }
}

export default AiReplyModal;