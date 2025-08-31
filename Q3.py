import turtle
import math

def draw_edge(t, length, depth):
    """
    Recursive function to draw one edge of the fractal polygon.
    :param t: turtle object
    :param length: length of the current segment
    :param depth: recursion depth
    """
    if depth == 0:
        t.forward(length)
    else:
        length /= 3.0
        # 1st segment
        draw_edge(t, length, depth - 1)
        # turn right for equilateral triangle pointing inward
        t.right(60)
        draw_edge(t, length, depth - 1)
        # turn left twice the angle (forming indentation inward)
        t.left(120)
        draw_edge(t, length, depth - 1)
        # turn back right
        t.right(60)
        draw_edge(t, length, depth - 1)

def draw_polygon(t, sides, length, depth):
    """
    Draws the fractal polygon.
    :param t: turtle object
    :param sides: number of sides of initial polygon
    :param length: side length
    :param depth: recursion depth
    """
    angle = 360.0 / sides
    for _ in range(sides):
        draw_edge(t, length, depth)
        t.right(angle)

# ---- Main Program ----
if __name__ == "__main__":
    # Get user input
    try:
        sides = int(input("Enter the number of sides: "))
        length = int(input("Enter the side length: "))
        depth = int(input("Enter the recursion depth: "))
    except ValueError:
        print("Please enter integer values.")
        raise SystemExit

    if sides < 3 or length <= 0 or depth < 0:
        print("Number of sides must be >= 3, length > 0 and depth >= 0.")
        raise SystemExit

    # Setup turtle
    screen = turtle.Screen()
    screen.title("Recursive Geometric Pattern")
    t = turtle.Turtle()
    t.speed(0)  # fastest

    # Move turtle to center drawing (simple placement)
    t.penup()
    t.setpos(-length/2, length/3)
    t.pendown()

    # Draw fractal polygon
    draw_polygon(t, sides, length, depth)

    t.hideturtle()
    # Keep window open
    turtle.done()
