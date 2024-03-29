# from https://towardsdatascience.com/particle-swarm-optimization-visually-explained-46289eeb2e14
import numpy as np

f = lambda x0, y0, x1, y1, w: (((x0 - x1) ** 2 + (y0 - y1) ** 2) ** 0.5) - w

class PSO:

    def __init__(self, particles, velocities, targets,
                 w=0.8, c_1=1, c_2=1, max_iter=100, prox_dist=.1, carry=0.01, auto_coef=True):
        self.particles = particles
        self.carry_cap = carry  # how much a particle can "carry" from target
        self.velocities = velocities
        # self.fitness_function = fitness_function
        self.targets = targets  # list of TARGET objs

        self.N = len(self.particles)
        self.w = w
        self.c_1 = c_1
        self.c_2 = c_2

        self.auto_coef = auto_coef
        self.max_iter = max_iter
        # defines how many particles must be near a target to decay
        self.decay_num = self.N * (1 - self.w) if 0 < w <= 1 else self.N
        self.decay_rad = prox_dist  # radius from target for decay

        self.p_bests = self.particles
        self.p_bests_values = self.fitness_function(self.particles)
        self.g_best = self.p_bests[0]
        self.g_best_value = self.p_bests_values[0]
        self.update_bests()

        self.iter = 0
        self.is_running = True
        self.has_targets = len(self.targets) > 0
        self.update_coef()

    def __str__(self):
        return f'[{self.iter}/{self.max_iter}] $w$:{self.w:.3f} - $c_1$:{self.c_1:.3f} - $c_2$:{self.c_2:.3f}'

    def fitness_function(self, pos):
        x, y = pos.swapaxes(0, 1)
        return self.f0(x, y)

    def f0(self, x, y):
        """ minimization function for n targets"""
        func_list = []
        for a in range(len(self.targets)):
            func_list.append(f(x, y, self.targets[a].x, self.targets[a].y, self.targets[a].weight))

        min_list = func_list[0] if len(func_list) > 0 else np.zeros((200, 200))
        for b in range(0, len(func_list)):
            min_list = np.minimum(min_list, func_list[b])
        return min_list

    def next(self):
        if self.iter > 0:
            self.move_particles()
            self.update_target()
            self.update_bests()
            self.update_coef()

        self.iter += 1
        self.is_running = self.is_running and self.has_targets and self.iter < self.max_iter
        return self.is_running

    def update_coef(self):
        if self.auto_coef:
            t = self.iter
            n = self.max_iter
            self.w = (0.4 / n ** 2) * (t - n) ** 2 + 0.4
            self.c_1 = -3 * t / n + 3.5
            self.c_2 = 3 * t / n + 0.5

    def update_target(self):
        """defines actions taken when targets are updating over time"""
        a = 0  # keeps track of index
        while a < len(self.targets):
            count = 0  # count is the number of particles within decay_rad
            for p in self.particles:
                euclid = (p[0] - self.targets[a].x) ** 2 + (p[1] - self.targets[a].y) ** 2
                if euclid < self.decay_rad:
                    count += 1
            if count >= self.decay_num:  # requires "convergence" on the target before decay
                self.targets[a].weight = self.targets[a].weight - (count * self.carry_cap) \
                    if self.targets[a].weight - (count * self.carry_cap) > 0 else 0
            if self.targets[a].weight == 0 and self.has_targets:
                self.remove_target(a)
                a = 0
                self.reset()
            else:
                self.targets[a].next()
                a += 1
            print(self.targets)

    def move_particles(self):

        # add inertia
        new_velocities = self.w * self.velocities
        # add cognitive component
        r_1 = np.random.random(self.N)
        r_1 = np.tile(r_1[:, None], (1, 2))
        new_velocities += self.c_1 * r_1 * (self.p_bests - self.particles)

        # add social component
        r_2 = np.random.random(self.N)
        r_2 = np.tile(r_2[:, None], (1, 2))
        g_best = np.tile(self.g_best[None], (self.N, 1))
        new_velocities += self.c_2 * r_2 * (g_best - self.particles)

        self.is_running = np.sum(self.velocities - new_velocities) != 0

        # update positions and velocities
        self.velocities = new_velocities
        self.particles = self.particles + new_velocities

    def update_bests(self):
        fits = self.fitness_function(self.particles)

        for i in range(len(self.particles)):
            # update best personnal value (cognitive)
            if fits[i] < self.p_bests_values[i]:
                self.p_bests_values[i] = fits[i]
                self.p_bests[i] = self.particles[i]

                # update best global value (social)
                if fits[i] < self.g_best_value:
                    self.g_best_value = fits[i]
                    self.g_best = self.particles[i]

    def remove_target(self, index):
        if len(self.targets) > 1:
            del self.targets[index]
        # This should flag when attempting to remove target, but only 1 target left
        else:  # if len(self.targets) == 1:
            self.has_targets = False

    def reset(self):
        """If target decays away, reset the swarm to search for other targets."""
        # randomize velocities again
        self.velocities = ((np.random.random((self.N, 2)) - 0.5) / 10)
        self.max_iter += 10
        self.p_bests = self.particles
        self.p_bests_values = self.fitness_function(self.particles)
        self.g_best = self.p_bests[0]
        self.g_best_value = self.p_bests_values[0]
        # self.update_bests()
