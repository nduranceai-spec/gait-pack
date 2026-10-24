import { get, writable } from 'svelte/store';

const profileKey = 'gait.person-profile.v1';

export interface PersonProfile {
  name: string;
  age: string;
  height: string;
  weight: string;
}

const blankProfile: PersonProfile = { name: '', age: '', height: '', weight: '' };

function loadProfile(): PersonProfile {
  if (typeof localStorage === 'undefined') return { ...blankProfile };
  try {
    const value = JSON.parse(localStorage.getItem(profileKey) || '{}') as Partial<PersonProfile>;
    return {
      name: typeof value.name === 'string' ? value.name : '',
      age: typeof value.age === 'string' ? value.age : '',
      height: typeof value.height === 'string' ? value.height : '',
      weight: typeof value.weight === 'string' ? value.weight : '',
    };
  } catch { return { ...blankProfile }; }
}

export const personProfile = writable<PersonProfile>(loadProfile());

personProfile.subscribe((profile) => {
  if (typeof localStorage !== 'undefined') localStorage.setItem(profileKey, JSON.stringify(profile));
});

export function validatePersonProfile(): PersonProfile {
  const profile = get(personProfile);
  const age = Number(profile.age), height = Number(profile.height), weight = Number(profile.weight);
  if (profile.name.trim().length < 2) throw new Error('Enter the person’s name before starting the test.');
  if (!Number.isFinite(age) || age < 1 || age > 120) throw new Error('Enter an age between 1 and 120.');
  if (!Number.isFinite(height) || height < 50 || height > 260) throw new Error('Enter a height in centimetres.');
  if (!Number.isFinite(weight) || weight < 10 || weight > 400) throw new Error('Enter a weight in kilograms.');
  return { name: profile.name.trim(), age: String(age), height: String(height), weight: String(weight) };
}
