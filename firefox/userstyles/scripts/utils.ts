import type { PortsSchema, UserstylesSchema } from "@/types/mod.ts";
import type { SetRequired } from "type-fest/source/set-required.d.ts";
import { PORTS_SCHEMA, REPO_ROOT, USERSTYLES_SCHEMA } from "@/constants.ts";

import * as yaml from "@std/yaml";
import * as path from "@std/path";

import Ajv, { type Schema } from "ajv";
import { log } from "@/logger.ts";
import { sprintf } from "@std/fmt/printf";

/**
 * @param content A string of YAML content
 * @param schema  A JSON schema
 * @returns A promise that resolves to the parsed YAML content, verified against the schema. Rejects if the content is invalid.
 */
export function validateYaml<T>(
  content: string,
  schema: Schema,
  file: string,
): T {
  const ajv = new Ajv.default();
  const validate = ajv.compile<T>(schema);
  const data = yaml.parse(content);

  if (!validate(data)) {
    log.error(
      validate.errors!.map((err) =>
        sprintf(
          "%s %s%s",
          err.instancePath.slice(1).replaceAll("/", "."),
          err.message,
          err.params.allowedValues
            ? ` (${JSON.stringify(err.params.allowedValues, undefined)})`
            : "",
        )
      ).join(" and "),
      {
        file,
      },
    );
    Deno.exit(1);
  }

  return data as T;
}

/**
 * Utility function that calls {@link validateYaml} on the userstyles.yml file.
 * Fails when data.userstyles is undefined.
 */
export function getUserstylesData(): Userstyles {
  const content = Deno.readTextFileSync(
    path.join(REPO_ROOT, "scripts/userstyles.yml"),
  );

  try {
    const data = validateYaml<UserstylesSchema.UserstylesSchema>(
      content,
      USERSTYLES_SCHEMA,
      "scripts/userstyles.yml",
    );

    for (const field of ["userstyles", "collaborators"] as const) {
      if (data[field] === undefined) {
        log.error(`Missing required field \`${field}\``, {
          file: "scripts/userstyles.yml",
        });
        Deno.exit(1);
      }
    }

    return data as Userstyles;
  } catch (err) {
    if (err instanceof Error && err.name === "SyntaxError") {
      const groups =
        /(?<message>.*) at line (?<line>\d+), column (?<column>\d+):[\S\s]*/
          .exec(err.message)?.groups;
      log.error(
        groups!.message,
        {
          file: "scripts/userstyles.yml",
          startLine: Number(groups!.line),
          content: content,
        },
      );
    } else {
      throw err;
    }

    Deno.exit(1);
  }
}

/**
 * Utility function that calls {@link validateYaml} on the ports.yml file.
 * Fails when data.userstyles is undefined.
 */
export async function getPortsData(): Promise<PortsSchema.PortsSchema> {
  const content = await fetch(
    "https://raw.githubusercontent.com/catppuccin/catppuccin/main/resources/ports.yml",
  ).then((res) => res.text());

  const data = validateYaml<PortsSchema.PortsSchema>(
    content,
    PORTS_SCHEMA,
    "ports.yml",
  );

  return data;
}

/**
 * Utility function that formats a list of items into the "x, y, ..., and z" format.
 * @example
 * formatListOfItems(['x']); // 'x'
 * @example
 * formatListOfItems(['x', 'y']); // 'x and y'
 * @example
 * formatListOfItems(['x', 'y', 'z']); // 'x, y, and z'
 */
export function formatListOfItems(items: unknown[]): string {
  // If there are two items, connect them with an "and".
  if (items.length === 2) return items.join(" and ");
  // Otherwise, there is either just one item or more than two items.
  return items.reduce((prev, curr, idx, arr) => {
    // If this is the first item of the items we are looping through, set our initial string to it.
    if (idx === 0) return curr;
    // If this is the last one, add a comma (Oxford commas are amazing) followed by "and" and the item to the string.
    if (curr === arr.at(-1)) return prev + `, and ${curr}`;
    // Otherwise, it is some item in the middle of the list and we can just add it as a comma followed by the item to the string.
    return prev + `, ${curr}`;
  }) as string;
}

type Userstyles = SetRequired<
  UserstylesSchema.UserstylesSchema,
  "userstyles" | "collaborators"
>;