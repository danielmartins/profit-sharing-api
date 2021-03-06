from decimal import Decimal

import pendulum


class Specification:
    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)

    def __xor__(self, other):
        return Xor(self, other)

    def __invert__(self):
        return Invert(self)

    def is_satisfied_by(self, candidate):
        raise NotImplementedError()

    def remainder_unsatisfied_by(self, candidate):
        if self.is_satisfied_by(candidate):
            return None
        else:
            return self


class CompositeSpecification(Specification):
    pass


class MultaryCompositeSpecification(CompositeSpecification):
    def __init__(self, *specifications):
        self.specifications = specifications

    def __repr__(self) -> str:
        repr = f" {self.__class__.__name__.split('.')[-1]} ".join(
            [str(s) for s in self.specifications]
        )
        return repr


class And(MultaryCompositeSpecification):
    def __and__(self, other):
        if isinstance(other, And):
            self.specifications += other.specifications
        else:
            self.specifications += (other,)
        return self

    def is_satisfied_by(self, candidate):
        satisfied = all(
            [
                specification.is_satisfied_by(candidate)
                for specification in self.specifications
            ]
        )
        return satisfied

    def remainder_unsatisfied_by(self, candidate):
        non_satisfied = [
            specification
            for specification in self.specifications
            if not specification.is_satisfied_by(candidate)
        ]
        if not non_satisfied:
            return None
        if len(non_satisfied) == 1:
            return non_satisfied[0]
        if len(non_satisfied) == len(self.specifications):
            return self
        return And(*non_satisfied)


class Or(MultaryCompositeSpecification):
    def __or__(self, other):
        if isinstance(other, Or):
            self.specifications += other.specifications
        else:
            self.specifications += (other,)
        return self

    def is_satisfied_by(self, candidate):
        satisfied = any(
            [
                specification.is_satisfied_by(candidate)
                for specification in self.specifications
            ]
        )
        return satisfied


class UnaryCompositeSpecification(CompositeSpecification):
    def __init__(self, specification):
        self.specification = specification


class Invert(UnaryCompositeSpecification):
    def is_satisfied_by(self, candidate):
        return not self.specification.is_satisfied_by(candidate)


class BinaryCompositeSpecification(CompositeSpecification):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class Xor(BinaryCompositeSpecification):
    def is_satisfied_by(self, candidate):
        return self.left.is_satisfied_by(candidate) ^ self.right.is_satisfied_by(
            candidate
        )


class NullaryCompositeSpecification(CompositeSpecification):
    pass


class TrueSpecification(NullaryCompositeSpecification):
    def is_satisfied_by(self, candidate):
        return True


class FalseSpecification(NullaryCompositeSpecification):
    def is_satisfied_by(self, candidate):
        return False


class DirectorBoard(Specification):
    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def is_satisfied_by(self, candidate):
        return candidate["area"].lower() == "diretoria"


class Trainee(Specification):
    def is_satisfied_by(self, candidate):
        return candidate["cargo"].lower() == "estagiario"


class AccountingDepartment(Specification):
    def is_satisfied_by(self, candidate):
        return candidate["area"].lower() == "contabilidade"


class FinancialDepartment(Specification):
    def is_satisfied_by(self, candidate):
        return candidate["area"].lower() == "financeiro"


class ITDepartment(Specification):
    def is_satisfied_by(self, candidate):
        return candidate["area"].lower() == "tecnologia"


class FacilitiesDepartment(Specification):
    def is_satisfied_by(self, candidate):
        return candidate["area"].lower() == "serviços gerais"


class CustomerExperienceDepartment(Specification):
    def is_satisfied_by(self, candidate):
        return candidate["area"].lower() == "relacionamento com o cliente"


class BaseSalaryCalculatorMixin(object):
    BASE_SALARY: Decimal = Decimal("1045.0")

    def __init__(self, threshold: int, base: Decimal = None) -> None:
        self._threshold = threshold
        if base:
            if not isinstance(base, Decimal):
                base = Decimal(base)
            self.BASE_SALARY = base

    def calculate(self, raw_salary):
        return raw_salary / self.BASE_SALARY

    def sanitize(self, raw_salary):
        if not isinstance(raw_salary, Decimal):
            raw_salary = Decimal(raw_salary)
        return raw_salary

    def __repr__(self):
        return f"{self.__class__.__name__}(threshold={self._threshold})"


class SalaryGreaterThan(BaseSalaryCalculatorMixin, Specification):
    def is_satisfied_by(self, candidate):
        return (
            self.calculate(self.sanitize(candidate["salario_bruto"])) > self._threshold
        )


class SalaryLessThan(BaseSalaryCalculatorMixin, Specification):
    def is_satisfied_by(self, candidate):
        return (
            self.calculate(self.sanitize(candidate["salario_bruto"])) < self._threshold
        )


class SalaryBetween(BaseSalaryCalculatorMixin, Specification):
    def __init__(self, first: int, second: int, base: Decimal = None) -> None:
        super().__init__(threshold=0, base=base)
        self._first = first
        self._second = second

    def is_satisfied_by(self, candidate):
        salaries = self.calculate(self.sanitize(candidate["salario_bruto"]))
        return self._first <= salaries <= self._second

    def __repr__(self):
        return f"{self.__class__.__name__}(first={self._first}, second={self._second})"


class AdmissionTimeInYearsLessThan(Specification):
    def __init__(self, threshold, current_time=None) -> None:
        super().__init__()
        self._threshold = threshold
        self._frozen = pendulum.parse(current_time) if current_time else pendulum.now()

    def is_satisfied_by(self, candidate):
        admission = pendulum.parse(candidate["data_de_admissao"])
        return admission.diff(self._frozen).in_years() < self._threshold

    def __repr__(self):
        return f"{self.__class__.__name__}(threshold={self._threshold}, current_time={self._frozen})"


class AdmissionTimeInYearsGreaterThan(Specification):
    def __init__(self, threshold, current_time=None) -> None:
        super().__init__()
        self._threshold = threshold
        self._frozen = pendulum.parse(current_time) if current_time else pendulum.now()

    def is_satisfied_by(self, candidate):
        admission = pendulum.parse(candidate["data_de_admissao"])
        return admission.diff(self._frozen).in_years() >= self._threshold

    def __repr__(self):
        return f"{self.__class__.__name__}(threshold={self._threshold}, current_time={self._frozen})"


class AdmissionTimeInYearsBetween(Specification):
    BASE_DAYS_ON_YEAR = 365

    def __init__(self, initial, final, current_time=None) -> None:
        super().__init__()
        self._initial_threshold = initial * self.BASE_DAYS_ON_YEAR
        self._end_threshold = final * self.BASE_DAYS_ON_YEAR
        self._frozen = pendulum.parse(current_time) if current_time else pendulum.now()

    def is_satisfied_by(self, candidate):
        admission = pendulum.parse(candidate["data_de_admissao"])
        diff_in_years = admission.diff(self._frozen).in_days()
        return self._initial_threshold < diff_in_years < self._end_threshold

    def __repr__(self):
        return f"{self.__class__.__name__}(initial={self._initial_threshold}, final={self._end_threshold})"
