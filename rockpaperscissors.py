import random
options = ["rock", "paper", "scissors"]
#h
global machinechoice
global playerchoice

def start2():
    global machinechoice
    global playerchoice
    playerchoice = input("Rock, paper, scissors... ").lower()
    machinechoice = random.choice(options)
    start()

def start():
    print("The machine chose...", machinechoice, "!")
    print()
    game()

def game():
    if machinechoice == playerchoice:
        print(f"Draw! You both selected {playerchoice}")
        end()

    elif playerchoice == "rock":
        if machinechoice == "paper":
            print("You lost! Paper beats rock.")
            end()
        elif machinechoice == "scissors":
            print("You won! Rock beats scissors.")
            end()
        else:
            print("damnnnn you messed up")
            quit()

    elif playerchoice == "paper":
        if machinechoice == "rock":
            print("You won! Paper beats rock, somehow.")
            end()
        elif machinechoice == "scissors":
            print("You lost! Scissors beat paper.")
            end()
        else:
            print("damnnnn you messed up")
            quit()

    elif playerchoice == "scissors":
        if machinechoice == "rock":
            print("You lost! Rock beats scissors.")
            end()
        elif machinechoice == "paper":
            print("You won! Scissors beat paper.")
            end()
        else:
            print("damnnnn you messed up")
            quit()
    
    else:
        print("uhhhhh")

def end():
    choice2 = input("Would you like to play again? (Y or N) ").lower()
    if choice2 == "y":
        print()
        start2()
    elif choice2 == "n":
        quit()
    else:
        end()

playerchoice = input("Rock, paper, scissors... ").lower()
machinechoice = random.choice(options)
start()