def initialize_population(rng, population_size, init_theta=None,
                          transfer_elites=None, mode="cold",
                          init_sigma=0.25, transfer_fraction=0.50,
                          n_theta=14):
    if mode == "cold":
        return [rng.normal(scale=1.0, size=n_theta)
                for _ in range(population_size)]

    if mode == "warm":
        population = [init_theta.copy()]
        while len(population) < population_size:
            population.append(init_theta + init_sigma * rng.normal(size=n_theta))
        return population

    if mode == "mixed":
        n_transfer = int(round(population_size * transfer_fraction))
        n_transfer = max(1, min(population_size - 1, n_transfer))
        population = [init_theta.copy()]
        while len(population) < n_transfer:
            population.append(init_theta + init_sigma * rng.normal(size=n_theta))
        while len(population) < population_size:
            population.append(rng.normal(scale=1.0, size=n_theta))
        rng.shuffle(population)
        return population

    if mode == "elite_warm":
        population = []
        while len(population) < population_size:
            base = transfer_elites[rng.integers(0, len(transfer_elites))]
            population.append(base + init_sigma * rng.normal(size=n_theta))
        return population

    if mode == "elite_mixed":
        n_transfer = int(round(population_size * transfer_fraction))
        n_transfer = max(1, min(population_size - 1, n_transfer))
        population = []
        for theta in transfer_elites:
            if len(population) < n_transfer:
                population.append(theta.copy())
        while len(population) < n_transfer:
            base = transfer_elites[rng.integers(0, len(transfer_elites))]
            population.append(base + init_sigma * rng.normal(size=n_theta))
        while len(population) < population_size:
            population.append(rng.normal(scale=1.0, size=n_theta))
        rng.shuffle(population)
        return population

    raise ValueError("Unknown initialization mode")
