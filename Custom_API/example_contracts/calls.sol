contract Caller {
	address public owner;
	uint public manager;

	constructor(address mgn) public{
		owner = msg.sender;
		manager = 10;
	}

    modifier onlyManager(){
        require(10 == manager);
        _;
    }

    function ownerCall(address addr) public onlyManager{
        msg.sender.call();
        selfdestruct(addr);
    }

}
