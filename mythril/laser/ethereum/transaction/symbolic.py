from z3 import BitVec, Extract, Not
from logging import debug

from mythril.disassembler.disassembly import Disassembly
from mythril.laser.ethereum.cfg import Node, Edge, JumpType
from mythril.laser.ethereum.state import CalldataType, Account, Calldata
from mythril.laser.ethereum.transaction.transaction_models import (
    MessageCallTransaction,
    ContractCreationTransaction,
    get_next_transaction_id,
)


def heuristic_message_call(laser_evm, callee_address: str, priority=None):
    if len(laser_evm.open_states) > 0 and len(laser_evm.open_states[0].transaction_sequence) == 2:
        heuristic_message_call_helper(laser_evm, callee_address, priority)
    else:
        execute_message_call(laser_evm, callee_address, priority)


def heuristic_message_call_helper(laser_evm, callee_address: str, priority=None):
    open_states = laser_evm.open_states[:]

    ranking = []
    first_order_work_list = ['RAW']
    second_order_work_list = ['WAR']
    third_order_work_list = ['WAW']
    forth_order_work_list = ['RAR']

    for open_state in laser_evm.open_states:
        for list in priority['RAW']:
            if open_state.node.function_name == list.first.function_name:
                laser_evm.first_order_work_list.append(open_state)
                laser_evm.open_states.remove(open_state)
                break
    laser_evm.ranking.append(laser_evm.first_order_work_list)

    for open_state in laser_evm.open_states:
        for list in priority['WAR']:
            if open_state.node.function_name == list.first.function_name:
                laser_evm.second_order_work_list.append(open_state)
                laser_evm.open_states.remove(open_state)
                break
    laser_evm.ranking.append(laser_evm.second_order_work_list)

    for open_state in laser_evm.open_states:
        for list in priority['WAW']:
            if open_state.node.function_name == list.first.function_name:
                laser_evm.third_order_work_list.append(open_state)
                laser_evm.open_states.remove(open_state)
                break
    laser_evm.ranking.append(laser_evm.third_order_work_list)

    for open_state in laser_evm.open_states:
        for list in priority['RAR']:
            if open_state.node.function_name == list.first.function_name:
                laser_evm.forth_order_work_list.append(open_state)
                laser_evm.open_states.remove(open_state)
                break
    laser_evm.ranking.append(laser_evm.forth_order_work_list)

    del laser_evm.open_states[:]

    for items in laser_evm.ranking:
        title = items[0]
        list1 = items[1:]

        for open_world_state in list1:
            if open_world_state[callee_address].deleted:
                debug("Can not execute dead contract, skipping.")
                continue

            last_func_called = open_world_state.node.function_name
            next_transaction_id = get_next_transaction_id()
            transaction = MessageCallTransaction(
                world_state=open_world_state,
                callee_account=open_world_state[callee_address],
                caller=BitVec("caller{}".format(next_transaction_id), 256),
                identifier=next_transaction_id,
                call_data=Calldata(next_transaction_id),
                gas_price=BitVec("gas_price{}".format(next_transaction_id), 256),
                call_value=BitVec("call_value{}".format(next_transaction_id), 256),
                origin=BitVec("origin{}".format(next_transaction_id), 256),
                call_data_type=CalldataType.SYMBOLIC,
            )

            # the open states from last iterations are appended to work list here
            _setup_global_state_for_execution(laser_evm, transaction, last_func_called)
        laser_evm.exec(priority=priority, title=title, laser_obj=laser_evm)

        if title == 'RAW':
            for gs in laser_evm.second_work_list:
                laser_evm.work_list.append(gs)
            laser_evm.exec(priority=priority, title=title, laser_obj=laser_evm)
        elif title == 'WAR':
            for gs in laser_evm.third_work_list:
                laser_evm.work_list.append(gs)
            laser_evm.exec(priority=priority, title=title, laser_obj=laser_evm)
        elif title == 'WAW':
            for gs in laser_evm.forth_work_list:
                laser_evm.work_list.append(gs)
            laser_evm.exec(priority=priority, title=title, laser_obj=laser_evm)


def execute_message_call(laser_evm, callee_address: str, priority=None) -> None:
    """ Executes a message call transaction from all open states """
    # TODO: Resolve circular import between .transaction and ..svm to import LaserEVM here
    # TODO: if the function of openstate.node.funcname is not in priority list, dont add it
    # TODO: This is for deleting repeated variables read
    # copy the open states from last iteration to this iteration
    # The working list is always empty when an iteration is done
    open_states = laser_evm.open_states[:]

    '''
    # if it is Call level 1, not unknown or not in priority "first", get rid of it
    if len(open_states) > 0  and open_states[0].transaction_sequence == 2:
        open_states = []


                for open_state in laser_evm.open_states[:]:
            func_visited = open_state.node.function_name
            if func_visited is in priority['RAW'].values().first.function_name

            for value in priority['RAW'].values():
                if func_visited == value.first.function_name:
                    open_states.append(open_state)
                    continue
            for value in priority['WAR'].values():
                if func_visited == value.first.function_name:
                    open_states.append(open_state)
                    continue

            for value in priority['WAW'].values():
                if func_visited == value.first.function_name:
                    open_states.append(open_state)
                    continue

            for value in priority['RAR'].values():
                if func_visited == value.first.function_name:
                    open_states.append(open_state)
                    continue
        '''


    del laser_evm.open_states[:]

    for open_world_state in open_states:
        if open_world_state[callee_address].deleted:
            debug("Can not execute dead contract, skipping.")
            continue

        next_transaction_id = get_next_transaction_id()
        transaction = MessageCallTransaction(
            world_state=open_world_state,
            callee_account=open_world_state[callee_address],
            caller=BitVec("caller{}".format(next_transaction_id), 256),
            identifier=next_transaction_id,
            call_data=Calldata(next_transaction_id),
            gas_price=BitVec("gas_price{}".format(next_transaction_id), 256),
            call_value=BitVec("call_value{}".format(next_transaction_id), 256),
            origin=BitVec("origin{}".format(next_transaction_id), 256),
            call_data_type=CalldataType.SYMBOLIC,
        )

        # the open states from last iterations are appended to work list here
        _setup_global_state_for_execution(laser_evm, transaction, open_world_state.node.function_name)

    laser_evm.exec(priority=priority)


def execute_contract_creation(
    laser_evm, contract_initialization_code, contract_name=None, priority=None
) -> Account:
    """ Executes a contract creation transaction from all open states"""
    # TODO: Resolve circular import between .transaction and ..svm to import LaserEVM here
    open_states = laser_evm.open_states[:]
    del laser_evm.open_states[:]

    new_account = laser_evm.world_state.create_account(
        0, concrete_storage=True, dynamic_loader=None
    )
    if contract_name:
        new_account.contract_name = contract_name

    for open_world_state in open_states:
        next_transaction_id = get_next_transaction_id()
        transaction = ContractCreationTransaction(
            open_world_state,
            BitVec("creator{}".format(next_transaction_id), 256),
            next_transaction_id,
            new_account,
            Disassembly(contract_initialization_code),
            [],
            BitVec("gas_price{}".format(next_transaction_id), 256),
            BitVec("call_value{}".format(next_transaction_id), 256),
            BitVec("origin{}".format(next_transaction_id), 256),
            CalldataType.SYMBOLIC,
        )
        _setup_global_state_for_execution(laser_evm, transaction)
    laser_evm.exec(True)

    return new_account


def _setup_global_state_for_execution(laser_evm, transaction, last_func_called=None) -> None:
    """ Sets up global state and cfg for a transactions execution"""
    # TODO: Resolve circular import between .transaction and ..svm to import LaserEVM here
    global_state = transaction.initial_global_state(last_func_called=last_func_called)
    global_state.transaction_stack.append((transaction, None))

    new_node = Node(global_state.environment.active_account.contract_name)

    laser_evm.nodes[new_node.uid] = new_node
    if transaction.world_state.node:
        laser_evm.edges.append(
            Edge(
                transaction.world_state.node.uid,
                new_node.uid,
                edge_type=JumpType.Transaction,
                condition=None,
            )
        )

        global_state.mstate.constraints += transaction.world_state.node.constraints
        new_node.constraints = global_state.mstate.constraints

    global_state.world_state.transaction_sequence.append(transaction)
    global_state.node = new_node
    new_node.states.append(global_state)
    laser_evm.work_list.append(global_state)
