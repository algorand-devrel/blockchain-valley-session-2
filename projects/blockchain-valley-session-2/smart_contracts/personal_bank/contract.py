from algopy import (
    ARC4Contract,
    UInt64,
    arc4,
    itxn,
    Global,
    LocalState,
    Txn,
    gtxn,
    op,
)


class PersonalBank(ARC4Contract):
    def __init__(self) -> None:
        self.balance = LocalState(UInt64)

    @arc4.abimethod(allow_actions=["OptIn"]) #외부에서 호출가능한 메소드다! 뒤에 decorator를 달 수 있음 -> allow_actions 같이, 호출하고 같이 실행되는 것
    def opt_in_to_app(self) -> None:  #OptIn을 시도했을 때 onComplete로 실행되는 함수
        self.balance[Txn.sender] = UInt64(0)   # Txn을 하는 sender의 Balance를 조회하고 그 값을 0으로 초기화

    @arc4.abimethod #decorator에 아무 것도 없으면 noOpt, 추가적으로 실행할 것이 없음
    def deposit(self, ptxn: gtxn.PaymentTransaction) -> UInt64:  # 스마트계약은 지갑이 없기 때문에 연동되는 지갑에 보내야함 -> 2개의 트랜잭션을 묶어줌 gtxn.PaymentTransaction
        assert ptxn.amount > 0, "Deposit amount must be greater than 0"  # assert 를 사용하여 호출하기 전에 맞는 상황인지 확인 
        #ptxn : 같이 묶인 트랜잭션 안에 amount 라는 property -> algo를 몇개 보낼것인지 그게 0이상인지
        assert (
            ptxn.receiver == Global.current_application_address  # Global.current ~  = 스마트 계약의 앱계정의 주소와 같은지 확인함
        ), "Deposit receiver must be the contract address"
        assert ptxn.sender == Txn.sender, "Deposit sender must be the caller"  # 돈을 보내는 사람이 이 계약을 호출하는 사람과 같은지 확인
        assert op.app_opted_in(  # Txn.sender = 메소드를 호출한 계정
            Txn.sender, Global.current_application_id  # 이 계정이 optIn이 되어있는지 체크 -> 스마트 계약이 optIn이 되었는지 -> 따라서 id를 확인
        ), "Deposit sender must opt-in to the app first."

        self.balance[Txn.sender] += ptxn.amount
        user_balance = self.balance[Txn.sender]  # 누구한테 얼마한테 받았는지 기록함 / 유저마다 다른 상태를 기록하므로 localState 사용

        return user_balance

    @arc4.abimethod(allow_actions=["CloseOut"])  # lcoal state 상태를 삭제, optOut 시킴 -> 묶였던 내 algo 수량도 풀림
    def withdraw(self) -> UInt64:
        userBalance = self.balance[Txn.sender]

        itxn.Payment(  # inner transaction 만들 수 있음, 그 중에서 algo를 보내는 payment
            receiver=Txn.sender,
            sender=Global.current_application_address,
            amount=userBalance,
            fee=0,  # 가스비, inner transaction도 가스비를 요구함, 설정을 한 해주면 앱 계정이 지불하게 됨, fee = 0 으로 설정해줘야 호출하는 사람이 가스비를 대신 지불함
        ).submit()

        return userBalance
