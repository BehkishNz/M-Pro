contract Suicide {
    address public owner;

    modifier onlyOwner{
      if(msg.sender != owner) revert();
      _;
    }

    function setOwner() public{
        owner = msg.sender;
    }

    function kill(address addr) public onlyOwner{
        selfdestruct(msg.sender);
    }
}
