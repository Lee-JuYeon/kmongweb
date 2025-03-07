/**
 * AiReplyViewModel ViewModel - 자동 답변 관련 비즈니스 로직 처리
 * 옵저버 패턴을 구현하여 데이터 변경 시 구독자에게 알림
 */
class AiReplyViewModel {
    constructor() {
        this.replies = {
            positive_basic: "로딩 중...",
            positive_detailed: "로딩 중...",
            negative_basic: "로딩 중...",
            negative_with_margin: "로딩 중...",
            alternative_solution: "로딩 중..."
        };
        this.observers = [];
        this.isLoading = false;
    }

    /**
     * 옵저버 추가aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
     * @param {Function} observer - 데이터 변경 시 호출될 콜백 함수
     */
    addObserver(observer) {
        this.observers.push(observer);
    }

    /**
     * 옵저버 제거
     * @param {Function} observer - 제거할 옵저버
     */
    removeObserver(observer) {
        this.observers = this.observers.filter(obs => obs !== observer);
    }

    /**
     * 모든 옵저버에게 현재 답변 데이터 알림
     */
    notifyObservers() {
        this.observers.forEach(observer => observer({
            replies: this.replies,
            isLoading: this.isLoading
        }));
    }

    /**
     * 답변 타입별 로딩 상태 설정
     * @param {boolean} isLoading - 로딩 상태
     */
    setLoading(isLoading) {
        this.isLoading = isLoading;
        this.notifyObservers();
    }

    /**
     * 특정 타입의 자동 답변 설정
     * @param {string} type - 답변 타입 (positive_basic, positive_detailed 등)
     * @param {string} text - 답변 텍스트
     */
    setReply(type, text) {
        if (this.replies.hasOwnProperty(type)) {
            this.replies[type] = text;
            this.notifyObservers();
        }
    }

    /**
     * 특정 타입의 자동 답변 가져오기
     * @param {string} type - 답변 타입
     * @returns {string} - 해당 타입의 답변 텍스트
     */
    getReply(type) {
        return this.replies[type] || "답변을 불러올 수 없습니다.";
    }

    /**
     * 모든 자동 답변 가져오기
     * @returns {Object} - 모든 답변 타입과 텍스트를 포함한 객체
     */
    getAllReplies() {
        return this.replies;
    }

    /**
     * 서버에서 특정 채팅방에 대한 GPT 자동 답변 가져오기
     * @param {string} chatroomId - 채팅방 ID
     * @returns {Promise} - 모든 답변 타입에 대한 데이터 로드를 완료하는 Promise
     */
    loadGptAnswers(chatroomId) {
        if (!chatroomId) {
            return Promise.reject("채팅방 ID가 없습니다.");
        }

        this.setLoading(true);

        const responseTypes = [
            "positive_basic",
            "positive_detailed",
            "negative_basic",
            "negative_with_margin",
            "alternative_solution"
        ];

        const promises = responseTypes.map(type => {
            return this._fetchGptAnswer(type, chatroomId)
                .then(answer => {
                    this.setReply(type, answer);
                    return { type, answer };
                })
                .catch(error => {
                    console.error(`${type} 답변 로드 중 오류:`, error);
                    this.setReply(type, "답변을 불러오는 데 실패했습니다.");
                    return { type, error };
                });
        });

        return Promise.all(promises)
            .finally(() => {
                this.setLoading(false);
            });
    }

    /**
     * 서버에서 특정 유형의 GPT 자동 답변 가져오기
     * @param {string} responseType - 답변 유형
     * @param {string} chatroomId - 채팅방 ID
     * @returns {Promise<string>} - GPT 답변 텍스트 Promise
     * @private
     */
    _fetchGptAnswer(responseType, chatroomId) {
        return fetch("/api/message/get_gpt_suggestions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                type: responseType,
                chatroom_id: chatroomId
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`서버 응답 오류: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            return data.answer || "답변이 생성되지 않았습니다.";
        });
    }
}

export default AiReplyViewModel;