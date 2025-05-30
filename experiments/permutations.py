# experiments/permutations.py
"""
Permutation generation strategies for option reordering.
"""
from typing import List
from collections import deque
import itertools


class PermutationGenerator:
    """Handles generation of option permutations."""
    
    @staticmethod
    def generate(permutation_type: str, 
                 original_labels: List[str] = None,
                 num_factorial: int = 24) -> List[List[str]]:
        """
        Generate permutations based on strategy.
        
        Args:
            permutation_type: 'circular' or 'factorial'
            original_labels: Labels to permute (default: ['A', 'B', 'C', 'D'])
            num_factorial: Number of factorial permutations to generate
            
        Returns:
            List of permutation lists
        """
        if original_labels is None:
            original_labels = ['A', 'B', 'C', 'D']
            
        if permutation_type == 'circular':
            return PermutationGenerator._generate_circular(original_labels)
        elif permutation_type == 'factorial':
            return PermutationGenerator._generate_factorial(original_labels, num_factorial)
        else:
            raise ValueError(f"Unknown permutation type: {permutation_type}")
    
    @staticmethod
    def _generate_circular(labels: List[str]) -> List[List[str]]:
        """Generate circular shift permutations."""
        if len(labels) != 4:
            raise ValueError("Circular permutations require exactly 4 labels")
            
        permutations = []
        items = deque(labels)
        
        for _ in range(len(labels)):
            permutations.append(list(items))
            items.rotate(1)  # Rotate right
            
        return permutations
    
    @staticmethod
    def _generate_factorial(labels: List[str], num_perms: int) -> List[List[str]]:
        """Generate factorial permutations."""
        num_perms = min(num_perms, 24)  # Max for 4 items
        perm_gen = itertools.islice(itertools.permutations(labels), num_perms)
        return [list(p) for p in perm_gen]

