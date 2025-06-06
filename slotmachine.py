import random

MAX_LINES = 3
MAX_BET = 1000
MIN_BET = 10

ROWS = 3
COLS = 3
symbol_count = {
    "A": 2,
    "B": 4,
    "C": 6,
    "D": 8
}
symbol_value = {
    "A": 5,
    "B": 4,
    "C": 3,
    "D": 2
}

def check_winnings(columns, lines, bet, value):
    winnings = 0
    winning_lines = []
    for line in range(lines):
        symbol = columns[0][line]
        for column in columns:
            if column[line] != symbol:
                break
        else:
            winnings += value[symbol] * bet
            winning_lines.append(line + 1)
    return winnings, winning_lines

def deposit():
    while True:
        amount = input("Enter the deposit: ")
        if amount.isdigit():
            amount = int(amount)
            if amount > 0:
                break
            else:
                print("Amount must be greater than 0.")
        else:
            print("Please enter a number.")
    return amount

def get_number_of_lines():
    while True:
        lines = input(f"Enter the number of lines to bet on (1-{MAX_LINES}): ")
        if lines.isdigit():
            lines = int(lines)
            if 1 <= lines <= MAX_LINES:
                break
            else:
                print("Enter a valid number.")
        else:
            print("Please enter a number.")
    return lines

def get_bet():
    while True:
        bet = input(f"Enter your BET for each line ({MIN_BET}-{MAX_BET}): ")
        if bet.isdigit():
            bet = int(bet)
            if MIN_BET <= bet <= MAX_BET:
                break
            else:
                print(f"Enter a value between Rs.{MIN_BET} and Rs.{MAX_BET}")
        else:
            print("Please enter a number.")
    return bet

def get_slot_machine_spin(rows, cols, symbol_count):
    all_symbols = []
    for symbol, count in symbol_count.items():
        all_symbols.extend([symbol] * count)
    
    columns = []
    for _ in range(cols):
        column = []
        current_symbols = all_symbols[:]
        for _ in range(rows):
            value = random.choice(current_symbols)
            current_symbols.remove(value)
            column.append(value)
        columns.append(column)
    return columns

def print_slot_machine(columns):
    for row in range(len(columns[0])):
        for i, column in enumerate(columns):
            if i != len(columns) - 1:
                print(column[row], end=" | ")
            else:
                print(column[row], end="")
        print()
#for every single row, we look through every col,and for every col we only print the curr row that we're on.
def main():
    balance = deposit()
    while True:
        print(f"Current balance is {balance}")
        lines = get_number_of_lines()
        while True:
            bet = get_bet()
            total_bet = bet * lines
            if total_bet > balance:
                print(f"You don't have enough to bet that amount, your current balance is {balance}")
            else:
                break
        
        print(f"You are placing a bet of {bet} on {lines} lines. Total bet is equal to: {total_bet}.")
        slots = get_slot_machine_spin(ROWS, COLS, symbol_count)
        print_slot_machine(slots)
        winnings, winning_lines = check_winnings(slots, lines, bet, symbol_value)
        print(f"You won ${winnings}.")
        print("You won on lines:", *winning_lines)
        
        balance += winnings - total_bet
        if balance <= 0:
            print("You have run out of money!")
            break
        
        play_again = input("Do you want to play again? (y/n): ")
        if play_again.lower() != 'y':
            break
    
    print(f"You left with ${balance}.")

main()
