from tools import  *
from objects import *
from routines import *


# ExampleBot2 is a more complex example to showcase how to put routines to use!

class ExampleBot(GoslingAgent):
    def run(agent):
        # This is just some code to warn us if we're offsides
        ball_dist_to_owngoal = (agent.ball.location - agent.friend_goal.location).magnitude()
        my_dist_to_owngoal = (agent.me.location - agent.friend_goal.location).magnitude()
        ball_closer_than_me = ball_dist_to_owngoal < my_dist_to_owngoal

        # If the stack currently has routines on it, we won't do anything else.
        # This first statement makes sure the stack is empty before evaluating what to do next
        # Maybe in the future, you could have it look for a better shot to take even as the current one is running???
        if len(agent.stack) < 1:

            # We want to run the kickoff routine if there's currently a kickoff.
            # The routine isn't very smart and doesn't consider if you have any teammates, so that would be something
            # to improve upon
            if agent.kickoff_flag:
                agent.push(kickoff())
            else:
                # If we're in match play, the first thing we do is create a dictionary of targets
                # I only have one for now, named "goal," that target's the opponent's goal
                targets = {"goal":(agent.foe_goal.left_post, agent.foe_goal.right_post)}

                # Once we have the dictionary complete, we pass it to the find_hits tool that looks into the future
                # to find potential shots to take
                shots = find_hits(agent, targets)

                # Time to push a routine. Let's see if we have any shots on goal we can take
                if len(shots["goal"]) > 0:
                    # We do, but is it any good? I want to "score" how good each shot is by its average speed vs how
                    # aligned we are for it!
                    def score_shot(x):
                        distance = (x.ball_location - agent.me.location).magnitude()
                        speed = distance / (x.intercept_time - agent.time)
                        return speed * x.ratio

                    best_shot = shots["goal"][0]
                    best_shot_score = score_shot(shots["goal"][0])
                    for shot in shots["goal"]:
                        score = score_shot(shot)
                        if score > best_shot_score:
                            best_shot = shot
                            best_shot_score = score

                    # So now we've found the "best" shot, but could we do better?
                    # It may be better to drive the car into a good position before taking a shot
                    agent.push(best_shot)

                # If there aren't any shots to take, we need to do something else.
                # Usually we can't take a shot because we don't have enough boost, so we'll look for a good boostpad
                # to grab.
                elif agent.me.boost < 30:
                    # These variables will keep track of the best boost we find to pick up
                    best_boost = None
                    best_boost_value = -1.0

                    # I want to find a boost that is between us and the goal. We'll determine this by making a vector
                    # pointing from us to each boost, and each boost to the goal, and see which is most similar
                    for boost in agent.boosts:
                        # We will ignore small or inactive boosts
                        if not boost.large: continue
                        if not boost.active: continue

                        # vector from us to boost
                        me_to_boost = (boost.location - agent.me.location).normalize()
                        # vector from boost to our goal
                        boost_to_goal = (agent.friend_goal.location - boost.location).normalize()

                        # Here's where we actually check to see if the current boost is better than the best so far.
                        # If it's more aligned , it becomes the new "best boost"
                        if boost_to_goal.dot(me_to_boost) > best_boost_value:
                            best_boost_value = boost_to_goal.dot(me_to_boost)
                            best_boost = boost
                    if best_boost is not None:
                        # Drive towards the best boost, but try to circle towards it so that we can go straight to our
                        # goal afterwards
                        agent.push(goto_boost(best_boost, agent.friend_goal.location))

                elif ball_closer_than_me and abs(agent.ball.location.x) < 2000:
                    # Okay, so if this code runs it means we don't have shots but we do have boost. The most likely
                    # Case is that we're offsides. We could make a new set of targets to clear the ball, but often
                    # a short_shot is good enough
                    agent.push(short_shot(agent.foe_goal.location))

                # if we still haven't found a routine, we should probably retreat towards our own goal.
                # Let's be smart though, heading towards the center of our goal might hit the ball into it.
                # Instead, we'll drive towards the nearest goalpost, and collect any small boost pads along the way
                if len(agent.stack) < 1:
                    left_dist = (agent.friend_goal.left_post - agent.me.location).magnitude()
                    right_dist = (agent.friend_goal.right_post - agent.me.location).magnitude()
                    if left_dist < right_dist:
                        target = agent.friend_goal.left_post
                    else:
                        target = agent.friend_goal.right_post

                    # I think it would be dumb to drive all the way back, and give the opponent a free ball
                    # so let's move the final target somwehere between the ball and the goal.

                    target_to_car = (agent.me.location - target).normalize()
                    target_to_ball = (agent.ball.location - target)
                    final_dist = target_to_car.dot(target_to_ball) * 0.5

                    # This moves our target point towards our car by 1/2 the distance of the target to the ball
                    # post-------car---------------------ball
                    target += target_to_car * final_dist

                    # This is a repeat of the earlier boost code, but with changes to work with small pads
                    # and restrict us from going backwards to get to a pad
                    best_boost = None
                    best_boost_value = -1.0

                    for boost in agent.boosts:
                        if not boost.active: continue
                        me_to_boost = (boost.location - agent.me.location).normalize()
                        boost_to_target = (target - boost.location).normalize()
                        if boost_to_target.dot(me_to_boost) > best_boost_value:
                            best_boost_value = boost_to_target.dot(me_to_boost)
                            best_boost = boost

                    if best_boost is not None and best_boost_value > 0.7 and agent.me.boost < 100:
                        agent.push(goto_boost(best_boost, target))
                    else:
                        # We couldn't find any boost pads to grab, so we just drive back slowly
                        relative_target = target - agent.me.location
                        distance = relative_target.magnitude()
                        local_target = agent.me.local(relative_target)
                        defaultPD(agent, local_target)
                        # this will drive at full speed towards the target, but slow down as we get closer
                        defaultThrottle(agent, cap(distance * 2, 0, 2300))

                        # gotta make sure it doesn't use boost in this case!
                        agent.controller.boost = False
